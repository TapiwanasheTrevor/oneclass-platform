# OneClass Platform - Zimbabwe Educational Management System

A comprehensive offline-first educational management platform designed for Zimbabwe's schools with multi-language support and robust student information systems.

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- PostgreSQL (local instance)
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/TapiwanasheTrevor/oneclass-platform.git
   cd oneclass-platform
   ```

2. **Start your local PostgreSQL**
   ```bash
   # Make sure PostgreSQL is running with:
   # Database: oneclass
   # User: postgres
   # Password: 123Bubblegums
   ```

3. **Start the development environment**
   ```bash
   ./scripts/start-dev.sh
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - MailHog (Email testing): http://localhost:8025

## 🏗️ Architecture

### Tech Stack
- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python
- **Database**: PostgreSQL (local)
- **Cache**: Redis (Docker)
- **Email**: MailHog (development)

### Services
- **Frontend**: React development server (port 3000)
- **Backend**: FastAPI server (port 8000)
- **Redis**: Caching layer (port 6379)
- **MailHog**: Email testing (ports 1025/8025)
- **PostgreSQL**: Local database (port 5432)

## 📋 Available Commands

### Development Scripts
```bash
# Start development environment
./scripts/start-dev.sh

# Stop development environment
./scripts/stop-dev.sh

# Reset development environment (removes containers and volumes)
./scripts/reset-dev.sh
```

### Docker Commands
```bash
# View service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart services
docker-compose restart

# Rebuild services
docker-compose build --no-cache

# Stop and remove everything
docker-compose down -v --remove-orphans
```

### Database Commands
```bash
# Connect to local PostgreSQL
psql -h localhost -U postgres -d oneclass

# Run database migrations
# (Execute SQL files in database/schemas/ directory)
```

## 🧪 Testing the SIS Module

The Student Information System (SIS) module is ready for testing:

```bash
# Health check
curl http://localhost:8000/api/v1/sis/health

# Get students
curl http://localhost:8000/api/v1/sis/students

# Get statistics
curl http://localhost:8000/api/v1/sis/stats

# Test with the standalone server
cd backend
python sis_server_with_db.py
```

## 🗂️ Project Structure

```
oneclass-platform/
├── backend/                 # FastAPI backend
│   ├── services/
│   │   └── sis/            # Student Information System
│   ├── requirements.txt
│   ├── Dockerfile
│   └── main.py
├── frontend/               # React frontend
│   ├── src/
│   │   └── components/
│   │       └── sis/       # SIS components
│   ├── package.json
│   └── Dockerfile
├── database/
│   └── schemas/           # Database schemas
├── scripts/               # Development scripts
├── docker-compose.yml     # Docker services
└── README.md
```

## 🔧 Configuration

### Environment Variables
Backend configuration is in `backend/.env`:
```env
DATABASE_URL=postgresql://postgres:123Bubblegums@localhost:5432/oneclass
REDIS_URL=redis://localhost:6379
SMTP_HOST=mailhog
SMTP_PORT=1025
```

### Database Schema
The SIS module uses PostgreSQL schemas:
- `platform.*` - Core platform tables
- `academic.*` - Academic management
- `sis.*` - Student Information System

## 📚 Development Guidelines

### Code Style
- Backend: Black formatter, flake8 linting
- Frontend: Prettier, ESLint
- Database: SQL with proper indexing

### VS Code Setup
Recommended extensions are configured in `.vscode/extensions.json`

## 🚨 Troubleshooting

### Common Issues

1. **Docker not starting**
   - Ensure Docker Desktop is running
   - Check Docker daemon status

2. **PostgreSQL connection errors**
   - Verify local PostgreSQL is running
   - Check database credentials
   - Ensure database `oneclass` exists

3. **Port conflicts**
   - Check if ports 3000, 8000, 6379 are available
   - Stop conflicting services

4. **Build failures**
   - Clear Docker cache: `docker system prune -a`
   - Rebuild containers: `docker-compose build --no-cache`

### Getting Help
- Check logs: `docker-compose logs -f`
- View service status: `docker-compose ps`
- Reset environment: `./scripts/reset-dev.sh`

## 🤝 Contributing

1. Follow the development setup
2. Create feature branches
3. Run tests before committing
4. Update documentation as needed

## 📄 License

Educational use - Zimbabwe Schools Platform

---

**Status**: Development Environment Ready ✅
**Last Updated**: July 2025