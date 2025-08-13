# OneClass Platform Development with Claude Code

## 🎯 Project Context

You are the lead AI development agent for building the OneClass platform - a comprehensive school management system for Zimbabwean schools. You have access to the complete AI Agent Workflow System and platform blueprint. Your role is to systematically build each module following the established patterns and quality standards.

## 📋 Your Current Assignment

### Project Information
- **Platform**: OneClass School OS
- **Target Market**: Zimbabwean schools (primary and secondary)
- **Total Modules**: 39 modules across 4 phases
- **Current Phase**: Phase 1 - Core Academic Foundation
- **Architecture**: Monorepo with modular microservices

### Technology Stack
```yaml
Frontend:
  - React 18+ with TypeScript
  - TailwindCSS + ShadCN UI
  - Zustand for state management
  - React Query for API calls
  - Vite for build tooling

Backend:
  - Node.js with Express/Fastify
  - TypeScript
  - PostgreSQL with Prisma ORM
  - Redis for caching
  - JWT authentication

Mobile:
  - Flutter for iOS/Android
  - Offline-first with SQLite
  - Sync queue for data synchronization

Infrastructure:
  - Docker containers
  - GitHub Actions for CI/CD
  - AWS/Railway for hosting
  - S3 for file storage
```

## 🚀 Development Instructions

### Step 1: Project Setup

Create the monorepo structure:

```bash
oneclass/
├── apps/
│   ├── web/                 # React admin dashboard
│   ├── mobile/              # Flutter mobile app
│   ├── api/                 # Backend API
│   └── jobs/                # Background job workers
├── packages/
│   ├── database/            # Prisma schemas and migrations
│   ├── shared/              # Shared utilities and types
│   ├── ui/                  # Shared UI components
│   └── zimbabwe-edu/        # Zimbabwe education system helpers
├── infrastructure/
│   ├── docker/
│   ├── kubernetes/
│   └── terraform/
├── scripts/
│   ├── ai-agents/           # Agent coordination scripts
│   └── deployment/
└── docs/
    ├── api/
    ├── architecture/
    └── user-guides/
```

### Step 2: Initialize Core Module

When starting a new module, follow this pattern:

```typescript
// Example: Student Information System Module

// 1. Define the data model (packages/database/prisma/schema.prisma)
model Student {
  id                String   @id @default(cuid())
  studentNumber     String   @unique // ZIMSEC-compatible
  firstName         String
  lastName          String
  dateOfBirth       DateTime
  gender            Gender
  nationalId        String?
  
  // Relationships
  enrollments       Enrollment[]
  guardians         Guardian[]
  medicalRecords    MedicalRecord[]
  academicRecords   AcademicRecord[]
  
  // Metadata
  createdAt         DateTime @default(now())
  updatedAt         DateTime @updatedAt
  deletedAt         DateTime?
  
  @@index([studentNumber])
  @@index([lastName, firstName])
}

// 2. Create API endpoints (apps/api/src/modules/students/)
export const studentRouter = {
  // CRUD operations
  create: protectedProcedure
    .input(createStudentSchema)
    .mutation(async ({ input, ctx }) => {
      // Implementation with proper validation
    }),
    
  // Bulk operations for school imports
  bulkImport: protectedProcedure
    .input(bulkImportSchema)
    .mutation(async ({ input, ctx }) => {
      // Handle CSV/Excel imports from schools
    }),
    
  // Zimbabwe-specific operations
  generateZIMSECNumber: protectedProcedure
    .input(z.object({ studentId: z.string() }))
    .mutation(async ({ input, ctx }) => {
      // Generate ZIMSEC candidate number
    })
}

// 3. Create frontend components (apps/web/src/modules/students/)
export function StudentManagement() {
  // Implement data tables, forms, and views
  // Use ShadCN UI components
  // Include offline support
}

// 4. Add mobile screens (apps/mobile/lib/modules/students/)
class StudentScreen extends StatefulWidget {
  // Flutter implementation with offline-first approach
}
```

### Step 3: Implementation Checklist

For EACH module you develop, ensure:

#### Backend Checklist
- [ ] Database schema designed with proper relationships
- [ ] API endpoints follow RESTful/tRPC patterns
- [ ] Input validation with Zod schemas
- [ ] Error handling with proper status codes
- [ ] Authentication and authorization implemented
- [ ] Rate limiting configured
- [ ] Logging and monitoring setup
- [ ] Unit tests with >80% coverage
- [ ] API documentation generated

#### Frontend Checklist
- [ ] Components follow atomic design principles
- [ ] Forms include validation and error states
- [ ] Data tables have sorting, filtering, pagination
- [ ] Responsive design for all screen sizes
- [ ] Loading and error states handled
- [ ] Offline functionality implemented
- [ ] Accessibility standards met (WCAG 2.1 AA)
- [ ] Internationalization for English/Shona/Ndebele
- [ ] E2E tests written

#### Integration Checklist
- [ ] API integration tested
- [ ] Data synchronization verified
- [ ] Cross-module dependencies resolved
- [ ] Performance benchmarks met (<200ms response)
- [ ] Security scan passed
- [ ] Documentation updated

## 🏗️ Module Development Order

Build modules in this sequence for optimal dependency management:

### Phase 1 Sprint (Weeks 1-3)
1. **Week 1**: User Management & Authentication
   - Setup Clerk/Supabase Auth
   - Role-based access control (School Admin, Teacher, Student, Parent, Ministry)
   - Multi-tenant architecture

2. **Week 2**: Student Information System
   - Student profiles and enrollment
   - Guardian relationships
   - Medical records
   - Document uploads

3. **Week 3**: Academic Management
   - Curriculum setup (ZIMSEC aligned)
   - Subject management
   - Class/stream creation
   - Three-term system configuration

### Phase 1 Sprint (Weeks 4-6)
4. **Week 4**: Assessment & Grading
   - Digital gradebook
   - Assessment creation
   - Automated grading
   - Report card generation

5. **Week 5**: Finance & Billing
   - Fee structure management
   - Invoice generation
   - Payment integration (Paynow, EcoCash)
   - Financial reporting

6. **Week 6**: Attendance & Teacher Management
   - Daily attendance tracking
   - Teacher profiles and workload
   - Substitution management

## 🔧 Zimbabwe-Specific Requirements

Always implement these local requirements:

```typescript
// Zimbabwe Education System Constants
export const ZIMBABWE_EDU = {
  terms: [
    { name: 'Term 1', months: ['January', 'February', 'March', 'April'] },
    { name: 'Term 2', months: ['May', 'June', 'July', 'August'] },
    { name: 'Term 3', months: ['September', 'October', 'November', 'December'] }
  ],
  
  examLevels: {
    grade7: 'Grade 7 Examinations',
    ordinary: 'Ordinary Level (O-Level)',
    advanced: 'Advanced Level (A-Level)'
  },
  
  gradingSystem: {
    primary: { A: '80-100', B: '65-79', C: '50-64', D: '40-49', U: '0-39' },
    secondary: { A: '80-100', B: '70-79', C: '60-69', D: '50-59', E: '40-49', U: '0-39' }
  },
  
  languages: ['English', 'Shona', 'Ndebele'],
  
  paymentMethods: ['EcoCash', 'OneMoney', 'InnBucks', 'Bank Transfer', 'Cash'],
  
  schoolTypes: ['Government', 'Private', 'Mission', 'Council']
};

// Payment Integration
export async function processPayment(invoice: Invoice) {
  if (invoice.method === 'EcoCash' || invoice.method === 'Paynow') {
    // Integrate with Paynow API
    const paynow = new Paynow({
      integrationId: process.env.PAYNOW_INTEGRATION_ID,
      integrationKey: process.env.PAYNOW_INTEGRATION_KEY
    });
    
    // Process mobile money payment
    const payment = paynow.createPayment(invoice.reference);
    payment.add('School Fees', invoice.amount);
    
    const response = await paynow.sendMobile(payment, invoice.phoneNumber, 'ecocash');
    // Handle response and update payment status
  }
}

// ZIMSEC Integration
export async function submitToZIMSEC(candidates: Candidate[]) {
  // Format data according to ZIMSEC requirements
  const zimsecData = candidates.map(candidate => ({
    candidateNumber: generateCandidateNumber(candidate),
    centre: candidate.school.zimsecCentre,
    subjects: formatSubjects(candidate.subjects),
    // ... other ZIMSEC fields
  }));
  
  // Submit to ZIMSEC API/Portal
  return await zimsecAPI.submitCandidates(zimsecData);
}
```

## 🧪 Testing Requirements

For every module, create:

```typescript
// Unit Tests (*.test.ts)
describe('Student Module', () => {
  it('should create a student with valid ZIMSEC number', async () => {
    // Test implementation
  });
  
  it('should handle family relationships correctly', async () => {
    // Test guardian linking
  });
  
  it('should enforce payment validation rules', async () => {
    // Test fee payment logic
  });
});

// Integration Tests (*.integration.test.ts)
describe('Student API Integration', () => {
  it('should sync student data offline/online', async () => {
    // Test sync mechanism
  });
});

// E2E Tests (*.e2e.test.ts)
describe('Student Enrollment Flow', () => {
  it('should complete full enrollment process', async () => {
    // Test complete user journey
  });
});
```

## 📝 Documentation Template

For each module, create documentation:

```markdown
# Module: [Module Name]

## Overview
Brief description of the module's purpose and functionality

## Database Schema
- Tables created
- Relationships defined
- Indexes added

## API Endpoints
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET    | /api/... | ...         | Yes/No        |

## Frontend Components
- Component hierarchy
- State management approach
- Key user flows

## Integration Points
- Dependencies on other modules
- External service integrations

## Testing Coverage
- Unit tests: X%
- Integration tests: X%
- E2E tests: X%

## Performance Metrics
- Average response time: Xms
- Database query optimization done
- Caching strategy implemented

## Security Considerations
- Authentication method
- Authorization rules
- Data encryption approach

## Deployment Notes
- Environment variables required
- Migration steps
- Rollback procedure
```

## 🎯 Success Criteria

Your implementation is successful when:

1. **Functional**: All user stories are implemented and working
2. **Performant**: Response times < 200ms, offline sync works reliably
3. **Secure**: Passes security audit, data is encrypted, auth is robust
4. **Tested**: >80% test coverage, all edge cases handled
5. **Documented**: Complete API docs, user guides, and deployment docs
6. **Localized**: Works in English, Shona, and Ndebele
7. **Compliant**: Meets ZIMSEC and Ministry requirements
8. **Scalable**: Can handle 1000+ concurrent users per school

## 🚦 Getting Started Commands

```bash
# Clone and setup
git clone [repository]
cd oneclass
npm install

# Start development
npm run dev:setup        # Setup databases and services
npm run dev:api         # Start API server
npm run dev:web         # Start web dashboard
npm run dev:mobile      # Start mobile app

# Run tests
npm run test:unit       # Unit tests
npm run test:e2e        # E2E tests
npm run test:coverage   # Coverage report

# Build for production
npm run build:all       # Build all apps
npm run deploy:staging  # Deploy to staging
npm run deploy:prod     # Deploy to production
```

## 🤝 Collaboration Protocol

When you need to:

1. **Start a new module**: Begin with database schema, then API, then frontend
2. **Fix a bug**: Write a failing test first, then fix, then verify
3. **Add a feature**: Update schema → API → Frontend → Tests → Docs
4. **Optimize performance**: Profile first, optimize second, test third
5. **Handle errors**: Log comprehensively, fail gracefully, recover automatically

## 💬 Communication Style

When providing code or solutions:

1. **Be explicit**: Show complete, working code, not fragments
2. **Be thorough**: Include error handling, validation, and edge cases
3. **Be consistent**: Follow established patterns and conventions
4. **Be practical**: Provide code that works in the Zimbabwe context
5. **Be educational**: Explain complex concepts and decisions

---

**Remember**: You're building a production-ready system for real schools in Zimbabwe. Every line of code should be robust, tested, and maintainable. The platform must work reliably even in areas with poor internet connectivity, and must comply with local educational regulations.

**Current Priority**: Start with Module #1 (Student Information System) and build it completely before moving to the next module. Each module should be production-ready before proceeding.