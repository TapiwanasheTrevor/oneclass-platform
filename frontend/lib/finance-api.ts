// =====================================================
// Finance API Client
// File: frontend/lib/finance-api.ts
// =====================================================

import { api } from './api';

export interface FeeCategory {
  id: string;
  name: string;
  code: string;
  description?: string;
  is_mandatory: boolean;
  is_refundable: boolean;
  allows_partial_payment: boolean;
  display_order: number;
  is_active: boolean;
}

export interface FeeStructure {
  id: string;
  name: string;
  description?: string;
  academic_year_id: string;
  grade_levels: number[];
  class_ids?: string[];
  is_default: boolean;
  applicable_from: string;
  applicable_to?: string;
  status: 'draft' | 'active' | 'inactive' | 'archived';
  total_amount?: number;
  items?: FeeItem[];
}

export interface FeeItem {
  id: string;
  name: string;
  description?: string;
  base_amount: number;
  currency: string;
  frequency: 'term' | 'annual' | 'monthly' | 'quarterly' | 'one_time';
  allows_installments: boolean;
  max_installments: number;
  late_fee_amount: number;
  fee_category_id: string;
  fee_category?: FeeCategory;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  student_id: string;
  student_name?: string;
  student_number?: string;
  grade_level?: string;
  invoice_date: string;
  due_date: string;
  academic_year_id: string;
  term_id?: string;
  subtotal: number;
  discount_amount: number;
  tax_amount: number;
  total_amount: number;
  paid_amount: number;
  outstanding_amount: number;
  payment_status: 'pending' | 'partial' | 'paid' | 'overdue';
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  currency: string;
  sent_to_parent: boolean;
  reminder_count: number;
  line_items?: InvoiceLineItem[];
}

export interface InvoiceLineItem {
  id: string;
  description: string;
  quantity: number;
  unit_price: number;
  discount_amount: number;
  line_total: number;
}

export interface Payment {
  id: string;
  payment_reference: string;
  student_id: string;
  student_name?: string;
  student_number?: string;
  amount: number;
  currency: string;
  payment_date: string;
  payment_method_id: string;
  payment_method?: PaymentMethod;
  transaction_id?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  payer_name?: string;
  payer_email?: string;
  payer_phone?: string;
  reconciled: boolean;
  notes?: string;
}

export interface PaymentMethod {
  id: string;
  name: string;
  code: string;
  type: 'cash' | 'mobile_money' | 'bank_transfer' | 'online' | 'card';
  is_active: boolean;
  requires_reference: boolean;
  supports_partial_payment: boolean;
  transaction_fee_percentage: number;
  transaction_fee_fixed: number;
  display_order: number;
  icon_url?: string;
}

export interface FinanceDashboard {
  school_id: string;
  academic_year_id: string;
  current_term_invoiced: number;
  current_term_collected: number;
  current_term_outstanding: number;
  current_term_collection_rate: number;
  year_to_date_invoiced: number;
  year_to_date_collected: number;
  year_to_date_outstanding: number;
  year_to_date_collection_rate: number;
  recent_payments: Payment[];
  overdue_invoices_count: number;
  pending_payments_count: number;
  monthly_collection_trend: Array<{
    month: string;
    expected: number;
    collected: number;
    rate: number;
  }>;
  payment_method_breakdown: Array<{
    method: string;
    amount: number;
    count: number;
    percentage: number;
  }>;
  fee_category_breakdown: Array<{
    category: string;
    amount: number;
    percentage: number;
  }>;
}

export interface PaynowPaymentRequest {
  student_id: string;
  invoice_ids: string[];
  amount: number;
  payer_email: string;
  payer_phone: string;
}

export interface PaynowPaymentResponse {
  payment_id: string;
  paynow_reference: string;
  poll_url: string;
  redirect_url: string;
  status: string;
  success: boolean;
  hash_valid: boolean;
}

// =====================================================
// FEE MANAGEMENT API
// =====================================================

export const financeApi = {
  // Fee Categories
  async getFeeCategories(activeOnly: boolean = true): Promise<FeeCategory[]> {
    const response = await api.get('/api/v1/finance/fee-management/categories', {
      params: { active_only: activeOnly }
    });
    return response.data;
  },

  async createFeeCategory(data: Partial<FeeCategory>): Promise<FeeCategory> {
    const response = await api.post('/api/v1/finance/fee-management/categories', data);
    return response.data;
  },

  async updateFeeCategory(id: string, data: Partial<FeeCategory>): Promise<FeeCategory> {
    const response = await api.put(`/api/v1/finance/fee-management/categories/${id}`, data);
    return response.data;
  },

  async deleteFeeCategory(id: string): Promise<void> {
    await api.delete(`/api/v1/finance/fee-management/categories/${id}`);
  },

  // Fee Structures
  async getFeeStructures(params?: {
    academic_year_id?: string;
    status?: string;
  }): Promise<FeeStructure[]> {
    const response = await api.get('/api/v1/finance/fee-management/structures', { params });
    return response.data;
  },

  async getFeeStructure(id: string): Promise<FeeStructure> {
    const response = await api.get(`/api/v1/finance/fee-management/structures/${id}`);
    return response.data;
  },

  async getFeeStructureDetails(id: string): Promise<{
    structure: FeeStructure;
    items: FeeItem[];
    total_amount: number;
  }> {
    const response = await api.get(`/api/v1/finance/fee-management/structures/${id}/details`);
    return response.data;
  },

  async createFeeStructure(data: Partial<FeeStructure>): Promise<FeeStructure> {
    const response = await api.post('/api/v1/finance/fee-management/structures', data);
    return response.data;
  },

  async updateFeeStructure(id: string, data: Partial<FeeStructure>): Promise<FeeStructure> {
    const response = await api.put(`/api/v1/finance/fee-management/structures/${id}`, data);
    return response.data;
  },

  async deleteFeeStructure(id: string): Promise<void> {
    await api.delete(`/api/v1/finance/fee-management/structures/${id}`);
  },

  // Fee Items
  async getFeeItems(structureId: string): Promise<FeeItem[]> {
    const response = await api.get(`/api/v1/finance/fee-management/structures/${structureId}/items`);
    return response.data;
  },

  async createFeeItem(structureId: string, data: Partial<FeeItem>): Promise<FeeItem> {
    const response = await api.post(`/api/v1/finance/fee-management/structures/${structureId}/items`, data);
    return response.data;
  },

  async updateFeeItem(id: string, data: Partial<FeeItem>): Promise<FeeItem> {
    const response = await api.put(`/api/v1/finance/fee-management/items/${id}`, data);
    return response.data;
  },

  async deleteFeeItem(id: string): Promise<void> {
    await api.delete(`/api/v1/finance/fee-management/items/${id}`);
  },

  // Student Fee Assignments
  async getStudentFeeAssignments(studentId: string): Promise<any[]> {
    const response = await api.get(`/api/v1/finance/fee-management/assignments/student/${studentId}`);
    return response.data;
  },

  async assignFeeStructure(data: {
    student_id: string;
    fee_structure_id: string;
    effective_from: string;
    discount_percentage?: number;
    discount_amount?: number;
    discount_reason?: string;
  }): Promise<any> {
    const response = await api.post('/api/v1/finance/fee-management/assignments', data);
    return response.data;
  },

  async bulkAssignFeeStructure(
    feeStructureId: string,
    studentIds: string[]
  ): Promise<any> {
    const response = await api.post('/api/v1/finance/fee-management/assignments/bulk-assign', {
      fee_structure_id: feeStructureId,
      student_ids: studentIds
    });
    return response.data;
  },

  async bulkAssignFeeStructureByGrade(
    feeStructureId: string,
    gradeLevels: number[]
  ): Promise<any> {
    const response = await api.post('/api/v1/finance/fee-management/assignments/bulk-assign-by-grade', {
      fee_structure_id: feeStructureId,
      grade_levels: gradeLevels
    });
    return response.data;
  },

  // =====================================================
  // INVOICES API
  // =====================================================

  async getInvoices(params?: {
    page?: number;
    page_size?: number;
    student_id?: string;
    grade_level?: number;
    payment_status?: string;
    academic_year_id?: string;
    term_id?: string;
    due_date_from?: string;
    due_date_to?: string;
  }): Promise<{
    invoices: Invoice[];
    total_count: number;
    page: number;
    page_size: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  }> {
    const response = await api.get('/api/v1/finance/invoices', { params });
    return response.data;
  },

  async getInvoice(id: string): Promise<Invoice> {
    const response = await api.get(`/api/v1/finance/invoices/${id}`);
    return response.data;
  },

  async createInvoice(data: {
    student_id: string;
    fee_structure_id: string;
    due_date: string;
    academic_year_id: string;
    term_id?: string;
    notes?: string;
  }): Promise<Invoice> {
    const response = await api.post('/api/v1/finance/invoices', data);
    return response.data;
  },

  async updateInvoice(id: string, data: {
    due_date?: string;
    notes?: string;
    status?: string;
  }): Promise<Invoice> {
    const response = await api.put(`/api/v1/finance/invoices/${id}`, data);
    return response.data;
  },

  async deleteInvoice(id: string): Promise<void> {
    await api.delete(`/api/v1/finance/invoices/${id}`);
  },

  async bulkGenerateInvoices(data: {
    fee_structure_id: string;
    due_date: string;
    academic_year_id: string;
    term_id?: string;
    student_ids?: string[];
    grade_levels?: number[];
    class_ids?: string[];
  }): Promise<{
    total_invoices_generated: number;
    total_students_processed: number;
    total_amount: number;
    failed_students: Array<{
      student_id: string;
      student_name: string;
      reason: string;
    }>;
    invoice_ids: string[];
  }> {
    const response = await api.post('/api/v1/finance/invoices/bulk-generate', data);
    return response.data;
  },

  async sendInvoice(id: string): Promise<void> {
    await api.post(`/api/v1/finance/invoices/${id}/send`);
  },

  async sendInvoiceReminder(id: string): Promise<void> {
    await api.post(`/api/v1/finance/invoices/${id}/send-reminder`);
  },

  // =====================================================
  // PAYMENTS API
  // =====================================================

  async getPayments(params?: {
    page?: number;
    page_size?: number;
    student_id?: string;
    payment_method_id?: string;
    status?: string;
    payment_date_from?: string;
    payment_date_to?: string;
    amount_min?: number;
    amount_max?: number;
    reconciled?: boolean;
  }): Promise<{
    payments: Payment[];
    total_count: number;
    page: number;
    page_size: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  }> {
    const response = await api.get('/api/v1/finance/payments', { params });
    return response.data;
  },

  async getPayment(id: string): Promise<Payment> {
    const response = await api.get(`/api/v1/finance/payments/${id}`);
    return response.data;
  },

  async createPayment(data: {
    student_id: string;
    payment_method_id: string;
    amount: number;
    currency?: string;
    payer_name?: string;
    payer_email?: string;
    payer_phone?: string;
    transaction_id?: string;
    notes?: string;
  }): Promise<Payment> {
    const response = await api.post('/api/v1/finance/payments', data);
    return response.data;
  },

  async updatePayment(id: string, data: {
    status?: string;
    transaction_id?: string;
    failure_reason?: string;
    notes?: string;
    reconciled?: boolean;
  }): Promise<Payment> {
    const response = await api.put(`/api/v1/finance/payments/${id}`, data);
    return response.data;
  },

  async allocatePayment(paymentId: string, invoiceIds: string[]): Promise<any> {
    const response = await api.post(`/api/v1/finance/payments/${paymentId}/allocate`, {
      invoice_ids: invoiceIds
    });
    return response.data;
  },

  // Payment Methods
  async getPaymentMethods(activeOnly: boolean = true): Promise<PaymentMethod[]> {
    const response = await api.get('/api/v1/finance/payments/methods', {
      params: { active_only: activeOnly }
    });
    return response.data;
  },

  async createPaymentMethod(data: Partial<PaymentMethod>): Promise<PaymentMethod> {
    const response = await api.post('/api/v1/finance/payments/methods', data);
    return response.data;
  },

  async updatePaymentMethod(id: string, data: Partial<PaymentMethod>): Promise<PaymentMethod> {
    const response = await api.put(`/api/v1/finance/payments/methods/${id}`, data);
    return response.data;
  },

  // =====================================================
  // PAYNOW INTEGRATION
  // =====================================================

  async initiatePaynowPayment(data: PaynowPaymentRequest): Promise<PaynowPaymentResponse> {
    const response = await api.post('/api/v1/finance/payments/paynow/initiate', data);
    return response.data;
  },

  async checkPaynowStatus(paymentId: string): Promise<any> {
    const response = await api.get(`/api/v1/finance/payments/paynow/status/${paymentId}`);
    return response.data;
  },

  async initiateMobilePayment(data: PaynowPaymentRequest & { method: 'ecocash' | 'onemoney' }): Promise<PaynowPaymentResponse> {
    const response = await api.post('/api/v1/finance/payments/paynow/mobile', data);
    return response.data;
  },

  // =====================================================
  // REPORTS API
  // =====================================================

  async getFinanceDashboard(academicYearId: string): Promise<FinanceDashboard> {
    const response = await api.get('/api/v1/finance/reports/dashboard', {
      params: { academic_year_id: academicYearId }
    });
    return response.data;
  },

  async getCollectionReport(params: {
    start_date: string;
    end_date: string;
    grade_levels?: number[];
    class_ids?: string[];
    fee_categories?: string[];
  }): Promise<any> {
    const response = await api.get('/api/v1/finance/reports/collection', { params });
    return response.data;
  },

  async getOutstandingReport(params?: {
    grade_levels?: number[];
    days_overdue_min?: number;
    amount_min?: number;
  }): Promise<any> {
    const response = await api.get('/api/v1/finance/reports/outstanding', { params });
    return response.data;
  },

  async exportFinancialReport(type: 'invoices' | 'payments' | 'outstanding' | 'collection', params?: any): Promise<Blob> {
    const response = await api.get(`/api/v1/finance/reports/export/${type}`, {
      params,
      responseType: 'blob'
    });
    return response.data;
  },

  async generateFinancialStatement(studentId: string, params?: {
    academic_year_id?: string;
    term_id?: string;
    format?: 'pdf' | 'html';
  }): Promise<Blob> {
    const response = await api.get(`/api/v1/finance/reports/statement/${studentId}`, {
      params,
      responseType: 'blob'
    });
    return response.data;
  },

  async generatePaymentReceipt(paymentId: string, format: 'pdf' | 'html' = 'pdf'): Promise<Blob> {
    const response = await api.get(`/api/v1/finance/reports/receipt/${paymentId}`, {
      params: { format },
      responseType: 'blob'
    });
    return response.data;
  }
};