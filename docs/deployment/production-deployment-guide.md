# OneClass Platform - Production Deployment Guide

This guide covers the complete production deployment of the OneClass Platform using Docker and Kubernetes.

## Overview

The OneClass Platform is designed for production deployment with:
- **Docker**: Containerized applications with multi-stage builds
- **Kubernetes**: Container orchestration with auto-scaling
- **Nginx**: Reverse proxy with SSL termination
- **PostgreSQL**: Primary database with backup system
- **Redis**: Caching and session storage
- **Monitoring**: Prometheus and Grafana for observability

## Prerequisites

### System Requirements
- **CPU**: 4+ cores (8+ recommended)
- **Memory**: 8GB+ RAM (16GB+ recommended)
- **Storage**: 100GB+ SSD storage
- **Network**: Public IP with domain access

### Software Requirements
- Docker 20.10+
- Docker Compose 2.0+
- Kubernetes 1.20+ (for K8s deployment)
- kubectl (for K8s deployment)
- Git

### Domain Requirements
- Primary domain: `oneclass.ac.zw`
- Wildcard SSL certificate for `*.oneclass.ac.zw`
- DNS configuration for subdomains

## Docker Deployment

### 1. Environment Setup

Clone the repository and set up environment files:

```bash
git clone <repository-url>
cd oneclass-platform

# Copy environment template
cp .env.production.example .env.production
```

### 2. Configure Environment Variables

Edit `.env.production` with your production values:

```bash
# Database
DB_PASSWORD=your-secure-database-password
REDIS_PASSWORD=your-secure-redis-password

# Authentication
JWT_SECRET=your-super-secure-jwt-secret-256-bits-minimum
CLERK_SECRET_KEY=sk_live_your-production-clerk-secret-key
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_your-production-clerk-publishable-key

# External Services
PAYNOW_INTEGRATION_ID=your-production-paynow-id
PAYNOW_INTEGRATION_KEY=your-production-paynow-key
OPENAI_API_KEY=sk-your-production-openai-api-key

# AWS S3 Storage
AWS_ACCESS_KEY_ID=AKIA_your_production_access_key
AWS_SECRET_ACCESS_KEY=your_production_secret_access_key
AWS_S3_BUCKET=oneclass-production-files

# Email
SMTP_HOST=smtp.gmail.com
SMTP_USER=noreply@oneclass.ac.zw
SMTP_PASSWORD=your-smtp-app-password

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
GRAFANA_PASSWORD=your-grafana-admin-password
```

### 3. SSL Certificate Setup

Place your SSL certificates in the `ssl/` directory:

```bash
mkdir -p ssl/
# Copy your SSL certificates
cp your-ssl-cert.crt ssl/oneclass.ac.zw.crt
cp your-ssl-key.key ssl/oneclass.ac.zw.key
```

### 4. Deploy with Docker Compose

```bash
# Deploy to production
chmod +x scripts/deploy.sh
./scripts/deploy.sh production

# Or manually with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### 5. Verify Deployment

Check service status:
```bash
docker-compose -f docker-compose.prod.yml ps
```

Access the application:
- Frontend: https://app.oneclass.ac.zw
- API: https://api.oneclass.ac.zw
- Admin: https://app.oneclass.ac.zw/admin
- Monitoring: http://localhost:3001 (Grafana)

## Kubernetes Deployment

### 1. Prerequisites Setup

Ensure you have a Kubernetes cluster and kubectl configured:

```bash
# Check cluster connection
kubectl cluster-info

# Check cluster resources
kubectl get nodes
```

### 2. Prepare Secrets

Create the secrets file:

```bash
cd k8s/
cp secrets.yaml.example secrets.yaml
```

Edit `secrets.yaml` with base64-encoded values:

```bash
# Encode secrets
echo -n "your-db-password" | base64
echo -n "your-redis-password" | base64
echo -n "your-jwt-secret" | base64
```

### 3. Deploy to Kubernetes

```bash
# Make deployment script executable
chmod +x k8s/deploy.sh

# Deploy the platform
./k8s/deploy.sh deploy production

# Or deploy manually
kubectl apply -f namespace.yaml
kubectl apply -f secrets.yaml
kubectl apply -f configmap.yaml
kubectl apply -f postgres-deployment.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f ingress.yaml
```

### 4. Verify Kubernetes Deployment

```bash
# Check deployment status
./k8s/deploy.sh status

# Check pods
kubectl get pods -n oneclass-platform

# Check services
kubectl get services -n oneclass-platform

# Check ingress
kubectl get ingress -n oneclass-platform
```

## DNS Configuration

### Required DNS Records

Configure the following DNS records:

```
# A Records
oneclass.ac.zw                IN  A  <your-server-ip>
api.oneclass.ac.zw           IN  A  <your-server-ip>
app.oneclass.ac.zw           IN  A  <your-server-ip>
admin.oneclass.ac.zw         IN  A  <your-server-ip>

# Wildcard for tenant subdomains
*.oneclass.ac.zw             IN  A  <your-server-ip>

# CNAME Records (optional)
www.oneclass.ac.zw           IN  CNAME  oneclass.ac.zw
```

### SSL Certificate Setup

For production, use Let's Encrypt or a commercial SSL certificate:

```bash
# Using certbot for Let's Encrypt
sudo certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials ~/.secrets/cloudflare.ini \
  -d oneclass.ac.zw \
  -d "*.oneclass.ac.zw"
```

## Monitoring and Observability

### Prometheus Metrics

The platform exposes metrics at:
- Backend: `/metrics`
- Frontend: `/api/metrics`

### Grafana Dashboards

Access Grafana at `http://localhost:3001` with:
- Username: `admin`
- Password: `${GRAFANA_PASSWORD}`

### Log Aggregation

Logs are available via:
```bash
# Docker logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend

# Kubernetes logs
kubectl logs -f deployment/backend -n oneclass-platform
kubectl logs -f deployment/frontend -n oneclass-platform
```

## Backup and Recovery

### Database Backup

Automated backups run daily at 2 AM:
```bash
# Manual backup
docker-compose -f docker-compose.prod.yml exec backup /backup.sh

# Restore from backup
docker-compose -f docker-compose.prod.yml exec postgres psql \
  -U oneclass -d oneclass_production < /backups/backup-file.sql
```

### File Storage Backup

Configure S3 backup for file uploads:
```bash
# Set environment variables
S3_BACKUP_BUCKET=oneclass-production-backups
AWS_ACCESS_KEY_ID=your-backup-access-key
AWS_SECRET_ACCESS_KEY=your-backup-secret-key
```

## Security Considerations

### Network Security
- Use HTTPS everywhere (SSL/TLS)
- Configure firewall rules
- Use private networks for internal communication
- Regular security updates

### Application Security
- Strong passwords and secrets
- Regular secret rotation
- Input validation and sanitization
- Rate limiting and DDoS protection

### Database Security
- Encrypted connections (SSL)
- Regular backups
- Access control and authentication
- Database activity monitoring

## Scaling and Performance

### Horizontal Scaling

Docker Compose scaling:
```bash
# Scale backend instances
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Scale frontend instances
docker-compose -f docker-compose.prod.yml up -d --scale frontend=3
```

Kubernetes auto-scaling is configured via HPA (Horizontal Pod Autoscaler).

### Performance Optimization

- Enable Redis caching
- Configure CDN for static assets
- Use database read replicas
- Implement connection pooling
- Enable gzip compression

## Maintenance

### Regular Tasks

1. **Daily**: Check system health and logs
2. **Weekly**: Review monitoring metrics
3. **Monthly**: Update dependencies and security patches
4. **Quarterly**: Review and rotate secrets

### Updates and Deployments

```bash
# Build new version
docker-compose -f docker-compose.prod.yml build

# Deploy with zero downtime
./scripts/deploy.sh production v1.2.3

# Rollback if needed
docker-compose -f docker-compose.prod.yml down
# Restore from backup
```

## Troubleshooting

### Common Issues

1. **Service not starting**: Check logs and environment variables
2. **Database connection**: Verify credentials and network connectivity
3. **SSL certificate**: Check certificate validity and paths
4. **Memory issues**: Monitor resource usage and scale accordingly

### Debug Commands

```bash
# Check service health
curl -f http://localhost:8000/health
curl -f http://localhost:3000/api/health

# Check database connection
docker-compose -f docker-compose.prod.yml exec postgres psql -U oneclass -d oneclass_production -c "SELECT 1;"

# Check Redis connection
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# View detailed logs
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
```

## Support and Maintenance

### Monitoring Alerts

Set up alerts for:
- High CPU/memory usage
- Database connection failures
- Application errors
- SSL certificate expiration

### Backup Verification

Regularly test backup restoration:
```bash
# Test database backup
./scripts/backup.sh
# Verify backup integrity
```

### Documentation Updates

Keep deployment documentation updated with:
- Configuration changes
- New environment variables
- Security updates
- Performance optimizations

## Conclusion

The OneClass Platform is now deployed and ready for production use. Regular monitoring, maintenance, and security updates are essential for optimal performance and reliability.

For support and questions, refer to the development team or create issues in the project repository.