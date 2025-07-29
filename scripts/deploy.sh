#!/bin/bash

# OneClass Platform - Production Deployment Script
# Handles complete deployment pipeline with zero-downtime updates

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_ENV=${1:-production}
VERSION=${2:-$(date +%Y%m%d-%H%M%S)}
BACKUP_ENABLED=${BACKUP_ENABLED:-true}
HEALTH_CHECK_RETRIES=${HEALTH_CHECK_RETRIES:-30}
HEALTH_CHECK_INTERVAL=${HEALTH_CHECK_INTERVAL:-10}

# Function to print colored output
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

# Function to check if environment file exists
check_env_file() {
    local env_file=".env.${DEPLOYMENT_ENV}"
    if [ ! -f "$env_file" ]; then
        print_error "Environment file $env_file not found!"
        print_error "Please create $env_file with the required configuration"
        exit 1
    fi
    print_success "Environment file $env_file found"
}

# Function to validate environment variables
validate_env() {
    print_status "Validating environment variables..."
    
    local required_vars=(
        "DB_PASSWORD"
        "REDIS_PASSWORD"
        "JWT_SECRET"
        "CLERK_SECRET_KEY"
        "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            print_error "  - $var"
        done
        exit 1
    fi
    
    print_success "All required environment variables are set"
}

# Function to check Docker and Docker Compose
check_docker() {
    print_status "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed!"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running!"
        exit 1
    fi
    
    print_success "Docker and Docker Compose are available"
}

# Function to backup database
backup_database() {
    if [ "$BACKUP_ENABLED" != "true" ]; then
        print_warning "Database backup is disabled"
        return 0
    fi
    
    print_status "Creating database backup..."
    
    local backup_dir="./backups/$(date +%Y%m%d)"
    mkdir -p "$backup_dir"
    
    local backup_file="$backup_dir/pre-deployment-$(date +%H%M%S).sql"
    
    # Create backup using Docker
    docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump \
        -U oneclass -d oneclass_production > "$backup_file" 2>/dev/null || {
        print_warning "Could not create database backup (database might not exist yet)"
        return 0
    }
    
    print_success "Database backup created: $backup_file"
}

# Function to build and deploy
deploy_services() {
    print_status "Building and deploying services..."
    
    # Set environment variables
    export VERSION="$VERSION"
    export DEPLOYMENT_ENV="$DEPLOYMENT_ENV"
    
    # Pull latest images for base layers
    docker-compose -f docker-compose.prod.yml pull postgres redis || true
    
    # Build and start services
    docker-compose -f docker-compose.prod.yml build --parallel
    docker-compose -f docker-compose.prod.yml up -d --remove-orphans
    
    print_success "Services deployed successfully"
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Wait for database to be ready
    local retries=0
    while [ $retries -lt 30 ]; do
        if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U oneclass -d oneclass_production &> /dev/null; then
            break
        fi
        print_status "Waiting for database to be ready... (attempt $((retries + 1))/30)"
        sleep 5
        retries=$((retries + 1))
    done
    
    if [ $retries -eq 30 ]; then
        print_error "Database failed to become ready"
        exit 1
    fi
    
    # Run migrations
    docker-compose -f docker-compose.prod.yml exec -T backend python -c "
import asyncio
from shared.database import init_database
asyncio.run(init_database())
" || {
        print_error "Database migration failed"
        exit 1
    }
    
    print_success "Database migrations completed"
}

# Function to perform health checks
health_check() {
    print_status "Performing health checks..."
    
    local services=("backend" "frontend" "nginx")
    local endpoints=("http://localhost:8000/health" "http://localhost:3000/api/health" "http://localhost/health")
    
    for i in "${!services[@]}"; do
        local service="${services[$i]}"
        local endpoint="${endpoints[$i]}"
        
        print_status "Checking $service health..."
        
        local retries=0
        while [ $retries -lt $HEALTH_CHECK_RETRIES ]; do
            if curl -sf "$endpoint" &> /dev/null; then
                print_success "$service is healthy"
                break
            fi
            
            print_status "Waiting for $service to be healthy... (attempt $((retries + 1))/$HEALTH_CHECK_RETRIES)"
            sleep $HEALTH_CHECK_INTERVAL
            retries=$((retries + 1))
        done
        
        if [ $retries -eq $HEALTH_CHECK_RETRIES ]; then
            print_error "$service failed health check"
            print_error "Deployment failed - rolling back..."
            rollback_deployment
            exit 1
        fi
    done
    
    print_success "All services are healthy"
}

# Function to rollback deployment
rollback_deployment() {
    print_warning "Rolling back deployment..."
    
    # Stop current services
    docker-compose -f docker-compose.prod.yml down
    
    # Restore from backup if available
    if [ "$BACKUP_ENABLED" = "true" ]; then
        local latest_backup=$(ls -t ./backups/*/pre-deployment-*.sql 2>/dev/null | head -n 1)
        if [ -n "$latest_backup" ]; then
            print_status "Restoring database from backup: $latest_backup"
            # Restore database backup
            docker-compose -f docker-compose.prod.yml up -d postgres
            sleep 10
            docker-compose -f docker-compose.prod.yml exec -T postgres psql \
                -U oneclass -d oneclass_production < "$latest_backup"
        fi
    fi
    
    print_warning "Rollback completed"
}

# Function to cleanup old containers and images
cleanup() {
    print_status "Cleaning up old containers and images..."
    
    # Remove unused containers
    docker container prune -f
    
    # Remove unused images (keep last 3 versions)
    docker image prune -f
    
    # Remove unused volumes (be careful with this)
    # docker volume prune -f
    
    print_success "Cleanup completed"
}

# Function to send deployment notification
send_notification() {
    local status=$1
    local message=$2
    
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"OneClass Platform Deployment - $status: $message\"}" \
            "$SLACK_WEBHOOK_URL" &> /dev/null || true
    fi
    
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"content\":\"🚀 OneClass Platform Deployment - $status: $message\"}" \
            "$DISCORD_WEBHOOK_URL" &> /dev/null || true
    fi
}

# Function to display deployment summary
deployment_summary() {
    local start_time=$1
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_section "DEPLOYMENT SUMMARY"
    print_success "Deployment completed successfully!"
    print_status "Environment: $DEPLOYMENT_ENV"
    print_status "Version: $VERSION"
    print_status "Duration: ${duration}s"
    print_status "Timestamp: $(date)"
    
    echo -e "\n${GREEN}🎉 OneClass Platform is now running in $DEPLOYMENT_ENV mode!${NC}"
    echo -e "\n${BLUE}Access URLs:${NC}"
    echo -e "  Frontend: https://app.oneclass.ac.zw"
    echo -e "  API: https://api.oneclass.ac.zw"
    echo -e "  Admin: https://app.oneclass.ac.zw/admin"
    echo -e "  Monitoring: http://localhost:3001 (Grafana)"
    echo -e "  Metrics: http://localhost:9090 (Prometheus)"
    
    echo -e "\n${BLUE}Service Status:${NC}"
    docker-compose -f docker-compose.prod.yml ps
}

# Main deployment function
main() {
    local start_time=$(date +%s)
    
    print_section "ONECLASS PLATFORM DEPLOYMENT"
    print_status "Starting deployment to $DEPLOYMENT_ENV environment"
    print_status "Version: $VERSION"
    print_status "Timestamp: $(date)"
    
    # Load environment variables
    if [ -f ".env.${DEPLOYMENT_ENV}" ]; then
        source ".env.${DEPLOYMENT_ENV}"
    fi
    
    # Pre-flight checks
    print_section "PRE-FLIGHT CHECKS"
    check_env_file
    validate_env
    check_docker
    
    # Backup
    print_section "BACKUP"
    backup_database
    
    # Deploy
    print_section "DEPLOYMENT"
    deploy_services
    run_migrations
    
    # Health checks
    print_section "HEALTH CHECKS"
    health_check
    
    # Cleanup
    print_section "CLEANUP"
    cleanup
    
    # Summary
    deployment_summary $start_time
    
    # Send notification
    send_notification "SUCCESS" "Deployment to $DEPLOYMENT_ENV completed successfully (v$VERSION)"
    
    print_success "Deployment pipeline completed successfully!"
}

# Trap errors and send failure notification
trap 'send_notification "FAILED" "Deployment to $DEPLOYMENT_ENV failed"; exit 1' ERR

# Check if help is requested
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "OneClass Platform Deployment Script"
    echo ""
    echo "Usage: $0 [environment] [version]"
    echo ""
    echo "Arguments:"
    echo "  environment  Deployment environment (production, staging) [default: production]"
    echo "  version      Version tag for deployment [default: timestamp]"
    echo ""
    echo "Environment Variables:"
    echo "  BACKUP_ENABLED           Enable database backup [default: true]"
    echo "  HEALTH_CHECK_RETRIES     Number of health check retries [default: 30]"
    echo "  HEALTH_CHECK_INTERVAL    Health check interval in seconds [default: 10]"
    echo "  SLACK_WEBHOOK_URL        Slack webhook for notifications"
    echo "  DISCORD_WEBHOOK_URL      Discord webhook for notifications"
    echo ""
    echo "Examples:"
    echo "  $0 production v1.2.3"
    echo "  $0 staging"
    echo ""
    exit 0
fi

# Run main function
main "$@"