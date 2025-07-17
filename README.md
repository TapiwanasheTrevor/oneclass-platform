# OneClass Platform

A comprehensive school management system for Zimbabwe's educational institutions.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd oneclass-platform
   ```

2. **Environment Setup**
   ```bash
   # Copy environment files
   cp .env.example .env.local
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env.local
   ```

3. **Backend Setup**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   cd ..
   ```

4. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

5. **Database Setup**
   ```bash
   # Start services
   docker-compose up -d postgres redis
   
   # Setup database
   ./database/scripts/setup-db.sh
   ```

6. **Start Development Servers**
   ```bash
   # Terminal 1: Backend
   cd backend && source .venv/bin/activate && python -m uvicorn shared.main:app --reload --port 8000
   
   # Terminal 2: Frontend
   cd frontend && npm run dev
   ```

## Project Structure

```
oneclass-platform/
├── backend/          # Python FastAPI backend
├── frontend/         # React TypeScript frontend
├── mobile/           # Flutter mobile app
├── database/         # Database schemas and migrations
├── docs/             # Documentation
├── infrastructure/   # Docker, K8s, Terraform
└── tools/            # Development tools and scripts
```

## Development

- **Backend**: FastAPI with PostgreSQL
- **Frontend**: React + TypeScript + Tailwind CSS
- **Mobile**: Flutter
- **Database**: PostgreSQL + Redis
- **Authentication**: Supabase

## Documentation

See the `docs/` directory for detailed documentation including:
- Technical specifications
- API documentation
- Development guides
- User manuals

## License

Private - All rights reserved