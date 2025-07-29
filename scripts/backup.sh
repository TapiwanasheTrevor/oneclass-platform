#!/bin/bash

# OneClass Platform - Database Backup Script
# Automated backup system for PostgreSQL database

set -e

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
POSTGRES_DB=${POSTGRES_DB:-oneclass_production}
POSTGRES_USER=${POSTGRES_USER:-oneclass}
POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
S3_BUCKET=${S3_BACKUP_BUCKET:-""}
COMPRESSION=${BACKUP_COMPRESSION:-"gzip"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup filename
BACKUP_FILE="$BACKUP_DIR/oneclass_backup_${TIMESTAMP}.sql"

log "Starting database backup..."

# Check if PostgreSQL is accessible
if ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; then
    error "PostgreSQL is not accessible at $POSTGRES_HOST:$POSTGRES_PORT"
    exit 1
fi

# Create database backup
log "Creating database dump..."
pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --format=custom \
    --compress=9 \
    --file="$BACKUP_FILE" || {
    error "Failed to create database backup"
    exit 1
}

# Verify backup file exists and has content
if [ ! -f "$BACKUP_FILE" ] || [ ! -s "$BACKUP_FILE" ]; then
    error "Backup file is empty or does not exist"
    exit 1
fi

success "Database backup created: $BACKUP_FILE"

# Compress backup if requested
if [ "$COMPRESSION" = "gzip" ]; then
    log "Compressing backup..."
    gzip "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    success "Backup compressed: $BACKUP_FILE"
fi

# Upload to S3 if configured
if [ -n "$S3_BUCKET" ]; then
    log "Uploading backup to S3..."
    if command -v aws &> /dev/null; then
        aws s3 cp "$BACKUP_FILE" "s3://$S3_BUCKET/backups/$(basename "$BACKUP_FILE")" || {
            warning "Failed to upload backup to S3"
        }
        success "Backup uploaded to S3: s3://$S3_BUCKET/backups/$(basename "$BACKUP_FILE")"
    else
        warning "AWS CLI not available, skipping S3 upload"
    fi
fi

# Calculate backup size
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
success "Backup size: $BACKUP_SIZE"

# Clean up old backups
log "Cleaning up old backups (retention: $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "oneclass_backup_*.sql*" -mtime +$RETENTION_DAYS -delete
OLD_BACKUPS_DELETED=$(find "$BACKUP_DIR" -name "oneclass_backup_*.sql*" -mtime +$RETENTION_DAYS | wc -l)
success "Deleted $OLD_BACKUPS_DELETED old backup files"

# Clean up old S3 backups if configured
if [ -n "$S3_BUCKET" ] && command -v aws &> /dev/null; then
    log "Cleaning up old S3 backups..."
    CUTOFF_DATE=$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d)
    aws s3 ls "s3://$S3_BUCKET/backups/" | while read -r line; do
        FILE_DATE=$(echo "$line" | awk '{print $1}')
        FILE_NAME=$(echo "$line" | awk '{print $4}')
        if [[ "$FILE_DATE" < "$CUTOFF_DATE" ]]; then
            aws s3 rm "s3://$S3_BUCKET/backups/$FILE_NAME" || true
            log "Deleted old S3 backup: $FILE_NAME"
        fi
    done
fi

# Send notification if webhook is configured
if [ -n "$BACKUP_WEBHOOK_URL" ]; then
    log "Sending backup notification..."
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"OneClass Platform backup completed successfully. Size: $BACKUP_SIZE\"}" \
        "$BACKUP_WEBHOOK_URL" &> /dev/null || {
        warning "Failed to send backup notification"
    }
fi

success "Backup process completed successfully!"

# Display backup summary
log "Backup Summary:"
log "  File: $BACKUP_FILE"
log "  Size: $BACKUP_SIZE"
log "  Timestamp: $TIMESTAMP"
log "  Retention: $RETENTION_DAYS days"
if [ -n "$S3_BUCKET" ]; then
    log "  S3 Bucket: $S3_BUCKET"
fi