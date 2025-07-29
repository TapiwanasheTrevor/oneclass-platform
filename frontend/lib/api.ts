// =====================================================
// Enhanced API Client with OneClass Backend Integration
// File: frontend/lib/api.ts
// =====================================================

import axios, { AxiosError, AxiosResponse } from 'axios';
import { toast } from 'sonner';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Error response interface from backend
interface ErrorResponse {
  success: false;
  error_code: string;
  message: string;
  user_message?: string;
  category: string;
  severity: string;
  details?: any;
  correlation_id?: string;
  suggestions?: string[];
  retry_possible?: boolean;
}

// Request interceptor to add auth token and school context
api.interceptors.request.use(
  (config) => {
    // Add auth token
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add school context if available
    const currentSchoolId = typeof window !== 'undefined' 
      ? localStorage.getItem('current_school_id') 
      : null;
    if (currentSchoolId) {
      config.headers['X-School-ID'] = currentSchoolId;
    }
    
    // Add correlation ID for tracking
    const correlationId = `web-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    config.headers['X-Correlation-ID'] = correlationId;
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors and success messages
api.interceptors.response.use(
  (response: AxiosResponse) => {
    // Handle success messages
    if (response.data?.message && response.status >= 200 && response.status < 300) {
      // Only show success toast for explicit success messages
      if (response.data.success !== false) {
        const method = response.config.method?.toUpperCase();
        if (['POST', 'PUT', 'DELETE'].includes(method || '')) {
          toast.success(response.data.message);
        }
      }
    }
    
    return response;
  },
  (error: AxiosError<ErrorResponse>) => {
    // Handle network errors
    if (!error.response) {
      toast.error('Network error. Please check your connection.');
      return Promise.reject(error);
    }
    
    const errorData = error.response.data;
    const status = error.response.status;
    
    // Handle authentication errors
    if (status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('current_school_id');
        
        // Only redirect if not already on login page
        if (!window.location.pathname.includes('/login')) {
          toast.error('Your session has expired. Please log in again.');
          window.location.href = '/login';
        }
      }
      return Promise.reject(error);
    }
    
    // Handle authorization errors
    if (status === 403) {
      const message = errorData?.user_message || 'You don\'t have permission to perform this action';
      toast.error(message);
      
      // Redirect to appropriate page based on error
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/unauthorized')) {
        window.location.href = '/unauthorized';
      }
      return Promise.reject(error);
    }
    
    // Handle validation errors (400, 422)
    if (status === 400 || status === 422) {
      const message = errorData?.user_message || errorData?.message || 'Please check your input and try again';
      toast.error(message);
      
      // Add validation error details to error object for form handling
      if (errorData?.errors) {
        error.validationErrors = errorData.errors;
      }
      return Promise.reject(error);
    }
    
    // Handle not found errors
    if (status === 404) {
      const message = errorData?.user_message || 'The requested resource was not found';
      toast.error(message);
      return Promise.reject(error);
    }
    
    // Handle conflict errors
    if (status === 409) {
      const message = errorData?.user_message || 'This operation conflicts with existing data';
      toast.error(message);
      return Promise.reject(error);
    }
    
    // Handle rate limiting
    if (status === 429) {
      const message = errorData?.user_message || 'Too many requests. Please try again later';
      const retryAfter = error.response.headers['retry-after'];
      const fullMessage = retryAfter ? `${message} (retry in ${retryAfter} seconds)` : message;
      toast.error(fullMessage);
      return Promise.reject(error);
    }
    
    // Handle server errors (5xx)
    if (status >= 500) {
      const message = errorData?.user_message || 'Something went wrong on our end. Please try again';
      toast.error(message);
      
      // Show retry suggestion if possible
      if (errorData?.retry_possible) {
        toast.info('You can try the operation again');
      }
      
      // Log correlation ID for debugging
      if (errorData?.correlation_id) {
        console.error(`Server error - Correlation ID: ${errorData.correlation_id}`);
      }
      
      return Promise.reject(error);
    }
    
    // Handle other errors
    const message = errorData?.user_message || errorData?.message || 'An unexpected error occurred';
    toast.error(message);
    
    return Promise.reject(error);
  }
);

// WebSocket connection for real-time updates
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 1000;
  private subscriptions: Set<string> = new Set();
  
  connect(token: string) {
    try {
      // For now, disable WebSocket connections to avoid connection errors
      // This can be re-enabled once the realtime service is properly configured
      console.log('WebSocket connection disabled for stability');
      return;

      const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/api/v1/realtime/ws?token=${token}`;
      console.log('Attempting WebSocket connection to:', wsUrl);

      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected successfully');
        this.reconnectAttempts = 0;

        // Resubscribe to operations
        if (this.subscriptions.size > 0) {
          this.send({
            type: 'subscribe',
            operation_ids: Array.from(this.subscriptions)
          });
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
    
    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.attemptReconnect(token);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }
  
  private attemptReconnect(token: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

      setTimeout(() => {
        this.connect(token);
      }, this.reconnectInterval * this.reconnectAttempts);
    } else {
      console.warn('Max WebSocket reconnection attempts reached. Real-time features will be disabled.');
    }
  }
  
  private handleMessage(data: any) {
    // Emit custom events for different message types
    const event = new CustomEvent('websocket-message', { detail: data });
    window.dispatchEvent(event);
    
    // Handle specific event types
    if (data.event_type === 'progress_update') {
      const progressEvent = new CustomEvent('progress-update', { detail: data.data });
      window.dispatchEvent(progressEvent);
    }
    
    if (data.event_type === 'operation_completed') {
      toast.success(data.message || 'Operation completed successfully');
    }
    
    if (data.event_type === 'error_occurred') {
      toast.error(data.message || 'An error occurred');
    }
  }
  
  subscribe(operationIds: string[]) {
    operationIds.forEach(id => this.subscriptions.add(id));
    
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.send({
        type: 'subscribe',
        operation_ids: operationIds
      });
    }
  }
  
  unsubscribe(operationIds: string[]) {
    operationIds.forEach(id => this.subscriptions.delete(id));
    
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.send({
        type: 'unsubscribe',
        operation_ids: operationIds
      });
    }
  }
  
  private send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
  
  disconnect() {
    this.ws?.close();
    this.ws = null;
    this.subscriptions.clear();
  }
}

// Global WebSocket manager instance
export const wsManager = new WebSocketManager();

// API helper functions
export const apiHelpers = {
  // Handle file uploads with progress tracking
  uploadFile: async (file: File, purpose: string, onProgress?: (progress: number) => void) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('purpose', purpose);
    
    return api.post('/api/v1/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
  },
  
  // Handle bulk operations with progress tracking
  bulkOperation: async (
    endpoint: string, 
    data: any, 
    onProgress?: (operationId: string) => void
  ) => {
    const response = await api.post(endpoint, data);
    
    if (response.data.operation_id && onProgress) {
      onProgress(response.data.operation_id);
      wsManager.subscribe([response.data.operation_id]);
    }
    
    return response;
  },
  
  // Get user context with school information
  getCurrentUser: () => api.get('/api/v1/auth/me'),
  
  // Switch school context
  switchSchool: (schoolId: string) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('current_school_id', schoolId);
    }
    return Promise.resolve();
  },
  
  // Health check
  healthCheck: () => api.get('/health'),
};

export default api;