# 1Class Local Development Setup Guide

## IDE Recommendation: **VS Code with Extensions**

### **Essential Extensions**
```bash
# Install via VS Code marketplace or command palette
code --install-extension ms-python.python
code --install-extension ms-python.black-formatter
code --install-extension ms-python.flake8
code --install-extension bradlc.vscode-tailwindcss
code --install-extension esbenp.prettier-vscode
code --install-extension ms-vscode.vscode-typescript-next
code --install-extension ms-vscode.vscode-json
code --install-extension humao.rest-client
code --install-extension ms-vscode-remote.remote-containers
code --install-extension ms-vscode.vscode-docker
code --install-extension ms-vscode.vscode-postgres
code --install-extension github.copilot
code --install-extension github.copilot-chat
```

### **VS Code Settings** (`.vscode/settings.json`)
```json
{
  "python.defaultInterpreterPath": "./backend/.venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "typescript.preferences.importModuleSpecifier": "relative",
  "tailwindCSS.experimental.classRegex": [
    ["cn\\(([^)]*)\\)", "'([^']*)'"],
    ["className\\s*:\\s*['\"`]([^'\"`]*)['\"`]"]
  ],
  "files.associations": {
    "*.sql": "sql"
  }
}
```

---

## Directory Structure

```
1class-platform/
├── README.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .env.local
├── .gitignore
├── .vscode/
│   ├── settings.json
│   ├── launch.json
│   └── extensions.json
│
├── docs/
│   ├── wiki/
│   │   ├── README.md                    # Master Index (synced to GitHub Wiki)
│   │   ├── session-recovery.md          # Quick start for new sessions
│   │   ├── architecture/
│   │   │   ├── database-design.md
│   │   │   ├── api-patterns.md
│   │   │   ├── frontend-patterns.md
│   │   │   └── offline-sync.md
│   │   ├── modules/
│   │   │   ├── module-01-core-admin.md
│   │   │   ├── module-09-sis.md
│   │   │   ├── module-10-finance.md
│   │   │   └── [other modules]
│   │   ├── development/
│   │   │   ├── setup-guide.md
│   │   │   ├── coding-standards.md
│   │   │   └── testing-strategies.md
│   │   └── sessions/
│   │       ├── 2024-12-19-sis-database.md
│   │       ├── 2024-12-20-sis-api.md
│   │       └── [session logs]
│   ├── api/
│   │   ├── openapi.yaml
│   │   └── postman-collections/
│   └── user-guides/
│       ├── admin-guide.md
│       ├── teacher-guide.md
│       └── parent-guide.md
│
├── database/
│   ├── migrations/
│   │   ├── 001_initial_schema.sql
│   │   ├── 002_sis_module.sql
│   │   └── 003_finance_module.sql
│   ├── schemas/
│   │   ├── 00_platform.sql
│   │   ├── 01_auth.sql
│   │   ├── 02_academic.sql
│   │   ├── 09_sis.sql
│   │   └── 10_finance.sql
│   ├── seed-data/
│   │   ├── development/
│   │   ├── test/
│   │   └── staging/
│   └── scripts/
│       ├── setup-db.sh
│       ├── reset-db.sh
│       └── backup-db.sh
│
├── backend/
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── .env.example
│   ├── .venv/
│   │
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── utils/
│   │   └── middleware/
│   │
│   ├── services/
│   │   ├── api-gateway/
│   │   │   ├── main.py
│   │   │   ├── routes/
│   │   │   └── middleware/
│   │   │
│   │   ├── sis/
│   │   │   ├── main.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── crud.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── students.py
│   │   │   │   ├── guardians.py
│   │   │   │   └── health.py
│   │   │   └── tests/
│   │   │       ├── test_models.py
│   │   │       ├── test_crud.py
│   │   │       └── test_routes.py
│   │   │
│   │   ├── academic/
│   │   │   ├── main.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── crud.py
│   │   │   ├── routes/
│   │   │   └── tests/
│   │   │
│   │   ├── finance/
│   │   │   ├── main.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── crud.py
│   │   │   ├── integrations/
│   │   │   │   ├── paynow.py
│   │   │   │   └── ecocash.py
│   │   │   ├── routes/
│   │   │   └── tests/
│   │   │
│   │   └── [other modules]/
│   │
│   └── tests/
│       ├── conftest.py
│       ├── integration/
│       └── e2e/
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   ├── Dockerfile
│   ├── .env.example
│   ├── index.html
│   │
│   ├── public/
│   │   ├── icons/
│   │   ├── images/
│   │   └── locales/
│   │       ├── en.json
│   │       ├── sn.json  # Shona
│   │       └── nd.json  # Ndebele
│   │
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── vite-env.d.ts
│   │   │
│   │   ├── components/
│   │   │   ├── ui/           # ShadCN components
│   │   │   │   ├── button.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── table.tsx
│   │   │   │   └── [shadcn components]
│   │   │   │
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   └── Dashboard.tsx
│   │   │   │
│   │   │   ├── sis/
│   │   │   │   ├── StudentRegistrationForm.tsx
│   │   │   │   ├── StudentProfile.tsx
│   │   │   │   ├── StudentList.tsx
│   │   │   │   └── GuardianManagement.tsx
│   │   │   │
│   │   │   ├── academic/
│   │   │   │   ├── DigitalMarkbook.tsx
│   │   │   │   ├── LessonPlanner.tsx
│   │   │   │   ├── AttendanceTracker.tsx
│   │   │   │   └── ClassManagement.tsx
│   │   │   │
│   │   │   ├── finance/
│   │   │   │   ├── InvoiceManagement.tsx
│   │   │   │   ├── PaymentForm.tsx
│   │   │   │   ├── FinancialReports.tsx
│   │   │   │   └── PaynowIntegration.tsx
│   │   │   │
│   │   │   └── [other modules]/
│   │   │
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useOfflineSync.ts
│   │   │   ├── useLocalStorage.ts
│   │   │   ├── useDebounce.ts
│   │   │   └── useZimbabweValidation.ts
│   │   │
│   │   ├── lib/
│   │   │   ├── utils.ts
│   │   │   ├── api.ts
│   │   │   ├── offline-manager.ts
│   │   │   ├── supabase.ts
│   │   │   ├── validations.ts
│   │   │   └── constants.ts
│   │   │
│   │   ├── stores/
│   │   │   ├── auth.ts
│   │   │   ├── offline.ts
│   │   │   └── app.ts
│   │   │
│   │   ├── types/
│   │   │   ├── api.ts
│   │   │   ├── auth.ts
│   │   │   ├── sis.ts
│   │   │   ├── academic.ts
│   │   │   └── finance.ts
│   │   │
│   │   └── styles/
│   │       ├── globals.css
│   │       └── components.css
│   │
│   └── tests/
│       ├── setup.ts
│       ├── components/
│       ├── integration/
│       └── e2e/
│
├── mobile/
│   ├── pubspec.yaml
│   ├── android/
│   ├── ios/
│   ├── lib/
│   │   ├── main.dart
│   │   ├── models/
│   │   ├── services/
│   │   ├── screens/
│   │   ├── widgets/
│   │   └── utils/
│   └── test/
│
├── infrastructure/
│   ├── docker/
│   │   ├── nginx/
│   │   ├── postgres/
│   │   └── redis/
│   ├── k8s/
│   │   ├── base/
│   │   ├── staging/
│   │   └── production/
│   ├── terraform/
│   │   ├── aws/
│   │   └── gcp/
│   └── scripts/
│       ├── deploy.sh
│       ├── backup.sh
│       └── monitoring.sh
│
└── tools/
    ├── scripts/
    │   ├── setup-dev.sh
    │   ├── run-tests.sh
    │   ├── db-migrate.sh
    │   └── generate-api-docs.sh
    ├── generators/
    │   ├── module-generator.py
    │   └── component-generator.js
    └── monitoring/
        ├── health-check.py
        └── performance-test.js
```

---

## Quick Setup Commands

### **1. Initial Setup**
```bash
# Clone and setup
git clone <your-repo>
cd 1class-platform

# Copy environment files
cp .env.example .env.local
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Make scripts executable
chmod +x tools/scripts/*.sh
chmod +x database/scripts/*.sh
```

### **2. Backend Setup**
```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt
```

### **3. Frontend Setup**
```bash
cd frontend

# Install dependencies
npm install

# Install development tools
npm install -D @types/node @vitejs/plugin-react
```

### **4. Database Setup**
```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres redis

# Run database setup
./database/scripts/setup-db.sh

# Apply initial migrations
./database/scripts/migrate.sh
```

### **5. Start Development Servers**
```bash
# Terminal 1: Backend services
cd backend && python -m uvicorn shared.main:app --reload --port 8000

# Terminal 2: Frontend dev server
cd frontend && npm run dev

# Terminal 3: Database and Redis
docker-compose up postgres redis

# Terminal 4: Mobile (optional)
cd mobile && flutter run
```

---

## Development Workflow Files

### **package.json Scripts** (Frontend)
```json
{
  "scripts": {
    "dev": "vite --port 3000",
    "build": "tsc && vite build",
    "test": "vitest",
    "test:e2e": "playwright test",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint . --ext ts,tsx --fix",
    "format": "prettier --write .",
    "type-check": "tsc --noEmit"
  }
}
```

### **pyproject.toml** (Backend)
```toml
[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
multi_line_output = 3

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### **docker-compose.yml**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: oneclass_dev
      POSTGRES_USER: oneclass
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/schemas:/docker-entrypoint-initdb.d

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"  # SMTP
      - "8025:8025"  # Web UI

volumes:
  postgres_data:
  redis_data:
```

---

## Essential Environment Variables

### **Backend (.env)**
```bash
# Database
DATABASE_URL=postgresql://oneclass:dev_password@localhost:5432/oneclass_dev
REDIS_URL=redis://localhost:6379

# Auth
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
JWT_SECRET=your_jwt_secret

# External Services
PAYNOW_INTEGRATION_ID=your_paynow_id
PAYNOW_INTEGRATION_KEY=your_paynow_key
OPENAI_API_KEY=your_openai_key

# Email
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=

# File Storage
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_S3_BUCKET=oneclass-dev-files
```

### **Frontend (.env.local)**
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_ENVIRONMENT=development
```

---

## Git Configuration

### **.gitignore**
```gitignore
# Environment files
.env
.env.local
.env.*.local

# Dependencies
node_modules/
.venv/
__pycache__/

# Build outputs
dist/
build/
*.pyc

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Database
*.db
*.sqlite
```

### **Pre-commit hooks** (`.pre-commit-config.yaml`)
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.0
    hooks:
      - id: prettier
        files: \.(js|ts|jsx|tsx|json|css|md)$
```

---

## Recommended Development Flow

### **Daily Workflow**
1. **Start**: `docker-compose up -d` (databases)
2. **Backend**: `cd backend && source .venv/bin/activate && python -m uvicorn shared.main:app --reload`
3. **Frontend**: `cd frontend && npm run dev`
4. **Code**: Work on current module using the technical specs
5. **Test**: `npm test` (frontend) and `pytest` (backend)
6. **Commit**: Pre-commit hooks ensure code quality

### **Module Development Pattern**
1. **Database**: Create schema in `database/schemas/`
2. **Backend**: Implement API in `backend/services/module/`
3. **Frontend**: Create components in `frontend/src/components/module/`
4. **Tests**: Write tests as you go
5. **Update Docs**: Keep technical specs current

This setup gives you everything needed for productive 1Class development with minimal friction and maximum code quality! 🚀