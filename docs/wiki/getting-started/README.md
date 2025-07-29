# Getting Started with OneClass Platform

## 🚀 Quick Start Guide

Welcome to the OneClass Platform! This guide will help you set up your development environment and get the platform running locally in under 30 minutes.

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your development machine:

### Required Software
- **Node.js**: Version 18.0.0 or higher
- **Python**: Version 3.11 or higher
- **PostgreSQL**: Version 15 or higher
- **Redis**: Version 7 or higher
- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher

### Development Tools (Recommended)
- **VS Code** with Python and TypeScript extensions
- **Git** for version control
- **Postman** for API testing
- **pgAdmin** or **DBeaver** for database management

### System Requirements
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 10GB free space
- **OS**: macOS, Linux, or Windows with WSL2

## 🛠️ Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/oneclass/platform.git
cd oneclass-platform
```

### 2. Environment Setup

#### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Frontend Setup
```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Or using yarn
yarn install
```

### 3. Database Setup

#### Using Docker (Recommended)
```bash
# Start PostgreSQL and Redis containers
docker-compose up -d postgres redis

# Wait for containers to be ready (about 30 seconds)
docker-compose logs postgres redis
```

#### Manual Installation
```bash
# Create database
createdb oneclass_platform

# Create Redis instance (default configuration)
redis-server --daemonize yes
```

### 4. Environment Configuration

#### Backend Environment Variables
Create `.env` file in the `backend` directory:

```bash
# Database Configuration
DATABASE_URL=postgresql://oneclass_user:oneclass_pass@localhost:5432/oneclass_platform

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Clerk Authentication
CLERK_SECRET_KEY=sk_test_your_clerk_secret_key_here
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_publishable_key_here

# Application Settings
SECRET_KEY=your-super-secret-key-here
DEBUG=True
ENVIRONMENT=development

# Email Configuration (Optional for development)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Monitoring (Optional)
ENABLE_MONITORING=True
PROMETHEUS_ENDPOINT=http://localhost:9090
```

#### Frontend Environment Variables
Create `.env.local` file in the `frontend` directory:

```bash
# Clerk Authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_publishable_key_here
CLERK_SECRET_KEY=sk_test_your_clerk_secret_key_here

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Development Settings
NODE_ENV=development
NEXT_PUBLIC_ENABLE_DEVTOOLS=true
```

### 5. Database Migration

```bash
# Navigate to backend directory
cd backend

# Run database migrations
alembic upgrade head

# Seed initial data (optional)
python scripts/seed_data.py
```

### 6. Start Development Servers

#### Terminal 1: Backend Server
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2: Frontend Server
```bash
cd frontend
npm run dev
# Or: yarn dev
```

### 7. Verify Installation

Open your browser and navigate to:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🎯 Development Workflow

### Daily Development Routine
1. **Pull Latest Changes**
   ```bash
   git pull origin main
   ```

2. **Update Dependencies**
   ```bash
   # Backend
   cd backend && pip install -r requirements.txt
   
   # Frontend
   cd frontend && npm install
   ```

3. **Run Database Migrations**
   ```bash
   cd backend && alembic upgrade head
   ```

4. **Start Development Servers**
   ```bash
   # Backend (Terminal 1)
   cd backend && uvicorn main:app --reload
   
   # Frontend (Terminal 2)
   cd frontend && npm run dev
   ```

### Creating New Features
1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow coding standards
   - Write tests for new functionality
   - Update documentation

3. **Run Tests**
   ```bash
   # Backend tests
   cd backend && pytest
   
   # Frontend tests
   cd frontend && npm test
   ```

4. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

## 🧪 Testing

### Backend Testing
```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run tests with verbose output
pytest -v
```

### Frontend Testing
```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Run E2E tests
npm run test:e2e
```

## 🔍 Debugging

### Backend Debugging
```bash
# Enable debug mode
export DEBUG=True

# Start with debugger
python -m debugpy --listen 5678 --wait-for-client -m uvicorn main:app --reload

# Or use VS Code launch configuration
```

### Frontend Debugging
```bash
# Enable debug mode
export NODE_ENV=development

# Start with debugger
npm run dev:debug

# Or use browser developer tools
```

### Common Issues and Solutions

#### Database Connection Issues
```bash
# Check if PostgreSQL is running
pg_ctl status

# Restart PostgreSQL
brew services restart postgresql  # macOS
sudo service postgresql restart   # Linux

# Check connection
psql -h localhost -U oneclass_user -d oneclass_platform
```

#### Redis Connection Issues
```bash
# Check if Redis is running
redis-cli ping

# Restart Redis
brew services restart redis  # macOS
sudo service redis restart   # Linux
```

#### Port Conflicts
```bash
# Check what's using port 8000
lsof -i :8000

# Kill process using port
kill -9 <PID>

# Use different port
uvicorn main:app --port 8001
```

## 📊 Monitoring Development

### Performance Monitoring
```bash
# Monitor API performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health

# Monitor database performance
psql -d oneclass_platform -c "SELECT * FROM pg_stat_activity;"

# Monitor memory usage
htop
```

### Log Monitoring
```bash
# Backend logs
tail -f backend/logs/app.log

# Frontend logs
npm run dev | grep -E "(error|warn)"

# Database logs
tail -f /var/log/postgresql/postgresql-15-main.log
```

## 🛡️ Security Setup

### SSL/TLS for Development
```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Start backend with HTTPS
uvicorn main:app --ssl-keyfile key.pem --ssl-certfile cert.pem --port 8443

# Start frontend with HTTPS
npm run dev -- --https --key key.pem --cert cert.pem
```

### Environment Security
```bash
# Set secure permissions on .env files
chmod 600 backend/.env frontend/.env.local

# Use environment variables instead of hardcoded values
export DATABASE_URL="postgresql://..."
```

## 🔄 Data Management

### Database Operations
```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "Add new table"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Reset database
alembic downgrade base
alembic upgrade head
```

### Data Seeding
```bash
# Seed development data
python scripts/seed_data.py

# Seed specific data
python scripts/seed_schools.py
python scripts/seed_users.py
python scripts/seed_students.py
```

## 🚀 Deployment Preparation

### Build Production Assets
```bash
# Build frontend
cd frontend
npm run build

# Test production build
npm run start

# Build backend
cd backend
pip install -r requirements.txt
python -m pytest
```

### Docker Development
```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📚 Learning Resources

### Documentation
- [Architecture Overview](../architecture/README.md)
- [API Documentation](../api/README.md)
- [Database Schema](../database/README.md)
- [Security Guide](../security/README.md)

### Video Tutorials
- Getting Started Walkthrough
- Development Environment Setup
- Building Your First Feature
- Testing and Debugging

### Community Resources
- [GitHub Discussions](https://github.com/oneclass/platform/discussions)
- [Discord Community](https://discord.gg/oneclass)
- [Developer Blog](https://blog.oneclass.ac.zw)

## 🆘 Getting Help

### Support Channels
- **GitHub Issues**: Bug reports and feature requests
- **Discord**: Real-time community support
- **Email**: dev-support@oneclass.ac.zw
- **Documentation**: Comprehensive guides and tutorials

### Troubleshooting Checklist
1. ✅ Check prerequisites are installed
2. ✅ Verify environment variables are set
3. ✅ Ensure database is running and accessible
4. ✅ Check Redis connection
5. ✅ Verify port availability
6. ✅ Review application logs
7. ✅ Check network connectivity
8. ✅ Validate authentication configuration

## 🎉 Next Steps

Now that you have the platform running locally, you can:

1. **Explore the Codebase**: Review the architecture and code structure
2. **Try the APIs**: Use the interactive API documentation at `/docs`
3. **Run Tests**: Execute the test suite to ensure everything works
4. **Create Your First Feature**: Follow the development workflow
5. **Join the Community**: Connect with other developers

Welcome to the OneClass Platform development community! 🚀

---

**Last Updated**: 2024-01-18
**Version**: 1.0.0
**Next Review**: 2024-02-18