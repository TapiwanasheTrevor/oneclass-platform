# Environment Configuration Guide

This guide explains how to properly configure environment variables for the OneClass Platform across different deployment environments.

## Overview

The OneClass Platform uses environment-specific configuration files to manage settings across development, staging, and production environments. Each environment has its own configuration template that should be customized for your specific deployment.

## Environment Files

### 1. Development Environment (`.env.development.example`)
- **Purpose**: Local development with relaxed security and mock services
- **Target**: Developer workstations and local testing
- **Features**: Hot reload enabled, mock services, debug logging, relaxed rate limiting

### 2. Staging Environment (`.env.staging.example`)
- **Purpose**: Pre-production testing with production-like settings
- **Target**: Staging servers and QA environments
- **Features**: Production security, test payment gateways, comprehensive monitoring

### 3. Production Environment (`.env.production.example`)
- **Purpose**: Live production deployment with maximum security
- **Target**: Production servers and live systems
- **Features**: Full security, real payment systems, performance optimization

## Quick Setup

### For Development

1. Copy the development template:
   ```bash
   cp .env.development.example .env.local
   ```

2. Update the following essential values:
   ```bash
   # Clerk Authentication
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your-key
   CLERK_SECRET_KEY=sk_test_your-key
   
   # Database (use local PostgreSQL)
   DATABASE_URL=postgresql://oneclass:dev_password@localhost:5432/oneclass_dev
   
   # Redis (use local Redis)
   REDIS_URL=redis://localhost:6379
   ```

### For Staging

1. Copy the staging template:
   ```bash
   cp .env.staging.example .env.staging
   ```

2. Update staging-specific values:
   ```bash
   # Use staging Clerk environment
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_staging-key
   CLERK_SECRET_KEY=sk_test_staging-key
   
   # Staging database
   DATABASE_URL=postgresql://staging_user:password@staging-db:5432/oneclass_staging
   
   # Test payment gateway
   PAYNOW_INTEGRATION_ID=test_paynow_id
   PAYNOW_INTEGRATION_KEY=test_paynow_key
   ```

### For Production

1. Copy the production template:
   ```bash
   cp .env.production.example .env.production
   ```

2. **CRITICAL**: Update all production values with real credentials:
   ```bash
   # Production Clerk environment
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_production-key
   CLERK_SECRET_KEY=sk_live_production-key
   
   # Production database with SSL
   DATABASE_URL=postgresql://prod_user:secure_password@prod-db:5432/oneclass_production
   
   # Real payment gateway
   PAYNOW_INTEGRATION_ID=real_paynow_id
   PAYNOW_INTEGRATION_KEY=real_paynow_key
   ```

## Security Considerations

### Development
- Use test credentials only
- Disable SSL verification for local development
- Enable debug logging
- Use mock services for external APIs

### Staging
- Use staging/test credentials
- Mirror production security settings
- Enable comprehensive monitoring
- Use test payment gateways

### Production
- **NEVER** use test credentials
- Enable all security features (SSL, HSTS, CSP)
- Use production payment gateways
- Enable audit logging and monitoring
- Regularly rotate secrets

## Required Environment Variables

### Core Application
```bash
NODE_ENV=production|staging|development
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_APP_URL=https://app.your-domain.com
```

### Authentication (Clerk)
```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
CLERK_WEBHOOK_SECRET=whsec_...
```

### Database (PostgreSQL)
```bash
DATABASE_URL=postgresql://user:password@host:port/database
DB_SSL=require  # for production
```

### Cache/Sessions (Redis)
```bash
REDIS_URL=redis://host:port
REDIS_PASSWORD=your-redis-password
```

### File Storage (AWS S3)
```bash
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=your-bucket-name
```

### Email (SMTP)
```bash
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587
SMTP_USER=your-email@domain.com
SMTP_PASSWORD=your-app-password
```

### Payment Gateway (Paynow)
```bash
PAYNOW_INTEGRATION_ID=your-integration-id
PAYNOW_INTEGRATION_KEY=your-integration-key
```

## Environment-Specific Features

### Development Features
- **Hot Reload**: Enabled for rapid development
- **Mock Services**: Use mock payments, SMS, and email
- **Debug Logging**: Detailed logs for troubleshooting
- **Relaxed Security**: Disabled CSRF, allowed HTTP
- **Demo Data**: Automatic database seeding

### Staging Features
- **Production Mirror**: Same security as production
- **Test Services**: Use test payment gateways
- **Full Monitoring**: Complete observability stack
- **Performance Testing**: Load testing capabilities
- **Integration Testing**: End-to-end test scenarios

### Production Features
- **Maximum Security**: HTTPS only, HSTS, CSP headers
- **Performance Optimization**: CDN, caching, compression
- **Monitoring & Alerts**: Real-time error tracking
- **Backup & Recovery**: Automated backups
- **Compliance**: GDPR, audit logging

## Deployment Scripts

### Development Setup
```bash
# Install dependencies
npm install

# Set up database
npm run db:setup

# Start development servers
npm run dev
```

### Staging Deployment
```bash
# Build application
npm run build

# Run database migrations
npm run db:migrate

# Start staging server
npm run start:staging
```

### Production Deployment
```bash
# Build optimized application
npm run build:production

# Run database migrations
npm run db:migrate:production

# Start production server
npm run start:production
```

## Environment Validation

Each environment file includes validation to ensure required variables are set:

```bash
# Check environment configuration
npm run env:validate

# Check staging environment
npm run env:validate:staging

# Check production environment
npm run env:validate:production
```

## Secrets Management

### Development
- Store in `.env.local` (gitignored)
- Use test/development credentials only
- Share common config through `.env.development.example`

### Staging/Production
- Use proper secrets management (AWS Secrets Manager, HashiCorp Vault)
- Never commit real credentials to version control
- Rotate secrets regularly
- Use environment-specific service accounts

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check `DATABASE_URL` format
   - Verify database server is running
   - Check firewall/security group settings

2. **Clerk Authentication Errors**
   - Verify publishable/secret key pair
   - Check webhook secret configuration
   - Ensure correct environment (test vs live)

3. **File Upload Failures**
   - Verify AWS credentials and permissions
   - Check S3 bucket configuration
   - Validate CORS settings

4. **Email Delivery Issues**
   - Check SMTP credentials
   - Verify email service configuration
   - Check spam/delivery settings

### Debug Commands

```bash
# Test database connection
npm run db:test

# Test Redis connection
npm run redis:test

# Test email configuration
npm run email:test

# Test file storage
npm run storage:test

# Validate all services
npm run services:validate
```

## Security Checklist

### Before Production Deployment

- [ ] All environment variables use production values
- [ ] No test/development credentials in production
- [ ] SSL/TLS certificates configured
- [ ] Database connections use SSL
- [ ] Secrets are properly managed (not in code)
- [ ] Monitoring and alerting configured
- [ ] Backup systems operational
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] Audit logging enabled

### Regular Maintenance

- [ ] Rotate database passwords quarterly
- [ ] Update API keys as needed
- [ ] Review and update security configurations
- [ ] Monitor for deprecated environment variables
- [ ] Test disaster recovery procedures
- [ ] Validate backup integrity

## Support

For environment configuration issues:

1. Check the troubleshooting section above
2. Review application logs for specific errors
3. Validate environment variables using provided scripts
4. Contact the development team with specific error messages

---

**Note**: This configuration guide is specific to the OneClass Platform. Always follow your organization's security policies and compliance requirements when configuring production environments.