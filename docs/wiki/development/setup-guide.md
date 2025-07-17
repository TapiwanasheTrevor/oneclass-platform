# OneClass Platform Development Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop
- Git
- VS Code (recommended)

## Initial Setup

### 1. Clone Repository
```bash
git clone https://github.com/TapiwanasheTrevor/oneclass-platform.git
cd oneclass-platform
```

### 2. Environment Configuration
```bash
# Copy environment templates
cp .env.example .env.local
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Edit .env files with your credentials
# Required: Supabase URL and keys
```

### 3. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 4. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Install additional dev tools if needed
npm install -D @types/node
```

### 5. Database Setup
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Wait for services to start
sleep 5

# Run database migrations
cd database
./scripts/setup-db.sh

# Seed development data (optional)
./scripts/seed-dev-data.sh
```

## Running the Application

### Option 1: Using VS Code Tasks
1. Open VS Code Command Palette (Ctrl/Cmd + Shift + P)
2. Run "Tasks: Run Task"
3. Select:
   - "Start Databases" first
   - "Start Backend"
   - "Start Frontend"

### Option 2: Manual Terminal Commands

**Terminal 1 - Databases:**
```bash
docker-compose up postgres redis
```

**Terminal 2 - Backend:**
```bash
cd backend
source .venv/bin/activate
python -m uvicorn shared.main:app --reload --port 8000
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
```

## Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MailHog**: http://localhost:8025
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Common Commands

### Backend
```bash
# Format code
black .

# Lint code
flake8

# Run tests
pytest

# Run specific test
pytest tests/test_students.py::test_create_student
```

### Frontend
```bash
# Format code
npm run format

# Lint code
npm run lint

# Type check
npm run type-check

# Run tests
npm test

# Build for production
npm run build
```

### Database
```bash
# Create new migration
./database/scripts/create-migration.sh "Add student documents table"

# Apply migrations
./database/scripts/migrate.sh

# Reset database
./database/scripts/reset-db.sh

# Backup database
./database/scripts/backup-db.sh
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :3000  # Mac/Linux
netstat -ano | findstr :3000  # Windows

# Kill process
kill -9 <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows
```

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker ps

# Check logs
docker logs oneclass-platform_postgres_1

# Restart services
docker-compose restart postgres
```

### Python Virtual Environment Issues
```bash
# Remove and recreate venv
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## VS Code Extensions

Install recommended extensions:
```bash
code --install-extension ms-python.python
code --install-extension ms-python.black-formatter
code --install-extension bradlc.vscode-tailwindcss
code --install-extension esbenp.prettier-vscode
```

## Git Workflow

### Feature Development
```bash
# Create feature branch
git checkout -b feature/sis-student-registration

# Make changes and commit
git add .
git commit -m "feat: add student registration form"

# Push to remote
git push -u origin feature/sis-student-registration
```

### Sync Wiki
```bash
# Run sync script
./tools/scripts/sync-wiki.sh

# Or use VS Code task
# Cmd/Ctrl + Shift + P -> "Tasks: Run Task" -> "Sync Wiki"
```

## Environment Variables Reference

### Backend (.env)
```env
DATABASE_URL=postgresql://oneclass:dev_password@localhost:5432/oneclass_dev
REDIS_URL=redis://localhost:6379
SUPABASE_URL=<your-supabase-url>
SUPABASE_ANON_KEY=<your-supabase-anon-key>
JWT_SECRET=<generate-secure-secret>
```

### Frontend (.env.local)
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=<your-supabase-url>
VITE_SUPABASE_ANON_KEY=<your-supabase-anon-key>
```

## Next Steps

1. Review the [SIS Module Specification](../modules/module-09-sis.md)
2. Set up your development environment
3. Start with the database schema
4. Implement API endpoints
5. Build frontend components

Happy coding! 🚀