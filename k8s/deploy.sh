#!/bin/bash

# OneClass Platform - Kubernetes Deployment Script
# Deploys the complete OneClass Platform to Kubernetes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
NAMESPACE="oneclass-platform"
DEPLOYMENT_ENV=${1:-production}
VERSION=${2:-latest}

# Functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo -e "\n${BLUE}==== $1 ====${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_section "CHECKING PREREQUISITES"
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed!"
        exit 1
    fi
    
    # Check if connected to cluster
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Not connected to Kubernetes cluster!"
        exit 1
    fi
    
    # Check if secrets file exists
    if [ ! -f "secrets.yaml" ]; then
        print_error "secrets.yaml not found!"
        print_error "Please create secrets.yaml from secrets.yaml.example"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Create namespace
create_namespace() {
    print_section "CREATING NAMESPACE"
    
    if kubectl get namespace $NAMESPACE &> /dev/null; then
        print_warning "Namespace $NAMESPACE already exists"
    else
        kubectl apply -f namespace.yaml
        print_success "Namespace $NAMESPACE created"
    fi
}

# Deploy secrets and configmaps
deploy_configs() {
    print_section "DEPLOYING CONFIGURATIONS"
    
    # Deploy secrets
    kubectl apply -f secrets.yaml
    print_success "Secrets deployed"
    
    # Deploy configmaps
    kubectl apply -f configmap.yaml
    print_success "ConfigMaps deployed"
}

# Deploy storage
deploy_storage() {
    print_section "DEPLOYING STORAGE"
    
    # Deploy PostgreSQL
    kubectl apply -f postgres-deployment.yaml
    print_success "PostgreSQL deployed"
    
    # Deploy Redis
    kubectl apply -f redis-deployment.yaml
    print_success "Redis deployed"
    
    # Wait for storage to be ready
    print_status "Waiting for storage to be ready..."
    kubectl wait --for=condition=Ready pod -l app=postgres -n $NAMESPACE --timeout=300s
    kubectl wait --for=condition=Ready pod -l app=redis -n $NAMESPACE --timeout=300s
    print_success "Storage is ready"
}

# Deploy applications
deploy_applications() {
    print_section "DEPLOYING APPLICATIONS"
    
    # Deploy backend
    kubectl apply -f backend-deployment.yaml
    print_success "Backend deployed"
    
    # Deploy frontend
    kubectl apply -f frontend-deployment.yaml
    print_success "Frontend deployed"
    
    # Wait for applications to be ready
    print_status "Waiting for applications to be ready..."
    kubectl wait --for=condition=Ready pod -l app=backend -n $NAMESPACE --timeout=300s
    kubectl wait --for=condition=Ready pod -l app=frontend -n $NAMESPACE --timeout=300s
    print_success "Applications are ready"
}

# Deploy ingress
deploy_ingress() {
    print_section "DEPLOYING INGRESS"
    
    # Deploy ingress
    kubectl apply -f ingress.yaml
    print_success "Ingress deployed"
    
    # Wait for ingress to be ready
    print_status "Waiting for ingress to be ready..."
    sleep 30
    print_success "Ingress is ready"
}

# Run database migrations
run_migrations() {
    print_section "RUNNING DATABASE MIGRATIONS"
    
    # Get backend pod
    BACKEND_POD=$(kubectl get pods -n $NAMESPACE -l app=backend -o jsonpath='{.items[0].metadata.name}')
    
    if [ -z "$BACKEND_POD" ]; then
        print_error "No backend pod found"
        exit 1
    fi
    
    # Run migrations
    kubectl exec -n $NAMESPACE $BACKEND_POD -- python -c "
import asyncio
from shared.database import init_database
asyncio.run(init_database())
"
    
    print_success "Database migrations completed"
}

# Health check
health_check() {
    print_section "HEALTH CHECKS"
    
    # Check pod status
    print_status "Checking pod status..."
    kubectl get pods -n $NAMESPACE
    
    # Check services
    print_status "Checking services..."
    kubectl get services -n $NAMESPACE
    
    # Check ingress
    print_status "Checking ingress..."
    kubectl get ingress -n $NAMESPACE
    
    print_success "Health checks completed"
}

# Display deployment info
deployment_info() {
    print_section "DEPLOYMENT INFORMATION"
    
    # Get ingress IP
    INGRESS_IP=$(kubectl get ingress oneclass-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    
    if [ -z "$INGRESS_IP" ]; then
        INGRESS_IP="<pending>"
    fi
    
    print_success "Deployment completed successfully!"
    print_status "Namespace: $NAMESPACE"
    print_status "Version: $VERSION"
    print_status "Ingress IP: $INGRESS_IP"
    
    echo -e "\n${GREEN}🎉 OneClass Platform is now running on Kubernetes!${NC}"
    echo -e "\n${BLUE}Access Information:${NC}"
    echo -e "  External IP: $INGRESS_IP"
    echo -e "  Domain: oneclass.ac.zw"
    echo -e "  API: api.oneclass.ac.zw"
    echo -e "  App: app.oneclass.ac.zw"
    
    echo -e "\n${BLUE}Useful Commands:${NC}"
    echo -e "  kubectl get pods -n $NAMESPACE"
    echo -e "  kubectl logs -f deployment/backend -n $NAMESPACE"
    echo -e "  kubectl logs -f deployment/frontend -n $NAMESPACE"
    echo -e "  kubectl describe ingress oneclass-ingress -n $NAMESPACE"
    
    echo -e "\n${YELLOW}Note: Make sure to update your DNS records to point to the ingress IP${NC}"
}

# Cleanup function
cleanup() {
    print_section "CLEANUP"
    
    read -p "Are you sure you want to delete the OneClass Platform deployment? [y/N] " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl delete namespace $NAMESPACE
        print_success "OneClass Platform deployment deleted"
    else
        print_status "Cleanup cancelled"
    fi
}

# Main function
main() {
    print_section "ONECLASS PLATFORM KUBERNETES DEPLOYMENT"
    print_status "Environment: $DEPLOYMENT_ENV"
    print_status "Version: $VERSION"
    print_status "Namespace: $NAMESPACE"
    
    check_prerequisites
    create_namespace
    deploy_configs
    deploy_storage
    deploy_applications
    deploy_ingress
    run_migrations
    health_check
    deployment_info
    
    print_success "Deployment completed successfully!"
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "cleanup")
        cleanup
        ;;
    "status")
        kubectl get all -n $NAMESPACE
        ;;
    "logs")
        kubectl logs -f deployment/${2:-backend} -n $NAMESPACE
        ;;
    "shell")
        POD=$(kubectl get pods -n $NAMESPACE -l app=${2:-backend} -o jsonpath='{.items[0].metadata.name}')
        kubectl exec -it $POD -n $NAMESPACE -- /bin/bash
        ;;
    "help")
        echo "OneClass Platform Kubernetes Deployment Script"
        echo ""
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  deploy     Deploy the OneClass Platform (default)"
        echo "  cleanup    Remove the OneClass Platform deployment"
        echo "  status     Show deployment status"
        echo "  logs       Show logs for a service"
        echo "  shell      Open shell in a pod"
        echo "  help       Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 deploy production v1.2.3"
        echo "  $0 logs backend"
        echo "  $0 shell frontend"
        echo "  $0 cleanup"
        ;;
    *)
        print_error "Unknown command: $1"
        print_status "Use '$0 help' for usage information"
        exit 1
        ;;
esac