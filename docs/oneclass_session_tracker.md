# OneClass Platform Technical Specifications - Master Index

## Project Status Dashboard
**Last Updated**: 2025-07-19
**Current Phase**: Core Module Development (39 Modules)
**Foundation Status**: ✅ COMPLETE
**Active Priority**: Student Information System (SIS) Module
**Completed Foundation**: Multi-tenant architecture, authentication, UI integration
**Next Priority**: Complete SIS Module Backend → Frontend → Testing

---

## Architecture Decisions Log
| Decision | Date | Rationale | Status |
|----------|------|-----------|--------|
| Multi-tenant Schema Design | 2024-XX-XX | Strong data isolation for schools | ✅ Decided |
| Offline-First Architecture | 2024-XX-XX | Zimbabwe connectivity challenges | ✅ Decided |
| PostgreSQL + Supabase Auth | 2024-XX-XX | Built-in RLS, JWT integration | ✅ Decided |
| React + Flutter Frontend | 2024-XX-XX | Web + Mobile unified experience | ✅ Decided |

---

## Module Development Status (39 Modules Total)

### ✅ **Foundation Completed**
- **Platform Infrastructure**: Multi-tenant architecture with school isolation ✅
- **Authentication System**: JWT with role-based access control ✅
- **User Management**: Multi-school memberships and invitations ✅
- **Frontend Framework**: React/Next.js with comprehensive UI ✅
- **Real-time Features**: WebSocket integration and progress tracking ✅
- **Error Handling**: Comprehensive error boundaries and recovery ✅

### 🚧 **Phase 1: Core Academic Foundation (In Progress)**
- **Module 1 (SIS)**: Database schema ✅ | API endpoints ⏳ | Frontend ⏳ | Tests ⏳
- **Module 2 (Academic)**: Planning ⏳ | Depends on SIS completion
- **Module 3 (Assessment)**: Planning ⏳ | Depends on Academic completion
- **Module 4 (Attendance)**: Planning ⏳ | Depends on SIS + Academic
- **Module 5 (Finance)**: Basic structure ✅ | Full implementation ⏳
- **Module 6 (Teachers)**: Planning ⏳ | Depends on Academic completion

### 📋 **Phase 2: Operations & Management (Planned)**
- Module 7: Parent Portal | Dependencies: SIS, Assessment, Attendance, Finance
- Module 8: Communication Hub | Dependencies: All user types
- Module 9: Timetable Management | Dependencies: Academic, Teachers
- Module 10: Report Generation | Dependencies: All data modules
- Module 11: User Management (Enhanced) | Dependencies: Core modules
- Module 12: System Administration | Dependencies: All operational modules

### 📋 **Phase 3: Enhanced Features (33 Modules Remaining)**
- Library Management, Inventory, Transport, Health Records
- Disciplinary Management, Extracurricular Activities
- AI Learning Assistant, Mobile Learning, E-Learning
- Advanced Analytics, Compliance Reporting, API Integrations
- *[See MODULE_DEVELOPMENT_SEQUENCE.md for complete list]*

---

## Session Recovery Quick Start

### **New Session Checklist**
1. Review [Current Development Status](#current-development-status)
2. Check [Last Session Summary](#last-session-summary)  
3. Load [Active Code Artifacts](#active-code-artifacts)
4. Continue from [Next Steps](#immediate-next-steps)

### **Current Development Status**
**Working On**: Student Information System (SIS) Module - Backend Development
**Progress**: Foundation complete, starting core module implementation
**Files Modified**: 
- `docs/SESSION_HANDOFF_CURRENT.md` ✅ Created comprehensive handoff doc
- `docs/MODULE_DEVELOPMENT_SEQUENCE.md` ✅ Created 39-module development plan
- `services/sis/` ✅ Basic structure exists, needs full implementation
- Authentication & UI foundation ✅ Complete and production-ready

### **Last Session Summary**
**Session**: Foundation & UI Integration Complete (July 19, 2025)
- **Accomplished**: Completed comprehensive platform foundation with multi-tenant architecture, authentication system, role-based UI, error handling, and mobile responsiveness
- **Decisions Made**: 39-module development sequence prioritizing SIS → Academic → Assessment as core foundation
- **Blockers Identified**: None - foundation is solid and ready for module development
- **Next Session Goals**: Complete SIS module backend with Zimbabwe-specific student data management

### **Active Code Artifacts**
- 📄 [Session Handoff Document](SESSION_HANDOFF_CURRENT.md) - Current project status
- 📄 [Module Development Sequence](MODULE_DEVELOPMENT_SEQUENCE.md) - 39-module roadmap
- 📄 [Platform Authentication](services/auth/) - Multi-school JWT system
- 📄 [Frontend Foundation](frontend/app/) - Role-based UI with error handling
- 📄 [SIS Module Structure](services/sis/) - Ready for full implementation

### **Immediate Next Steps**
1. **Complete SIS Backend**: Expand CRUD operations for students, guardians, enrollment
2. **Zimbabwe Integration**: Add National ID, Birth Certificate, local phone validation
3. **Family Relationships**: Implement parent-student linking with proper constraints
4. **Bulk Operations**: Add import/export functionality for existing school data
5. **SIS Frontend**: Build comprehensive student management interface

---

## Technical Standards & Patterns

### **Database Patterns**
```sql
-- Multi-tenant table template
CREATE TABLE module_name.entity_name (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES platform.schools(id),
    -- entity fields here
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS policy template  
CREATE POLICY select_school_data ON module_name.entity_name
FOR SELECT TO authenticated_user
USING (school_id = (SELECT school_id FROM platform.users WHERE id = auth.uid()));
```

### **API Patterns**
```python
# FastAPI endpoint template
@router.post("/entities", response_model=EntityResponse, status_code=201)
async def create_entity(
    entity_data: EntityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    # Standard permission check
    if not user_has_permission(current_user, ["admin", "teacher"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Business logic here
    result = await crud.create_entity(db, entity_data, current_user.school_id)
    return result
```

### **Frontend Patterns**
```typescript
// React component template with offline sync
export function EntityForm() {
  const { data, isLoading } = useQuery(['entities'], fetchEntities);
  const { mutate, isPending } = useMutation({
    mutationFn: createEntity,
    onSuccess: () => {
      toast({ title: "Success", description: "Entity created successfully" });
      queryClient.invalidateQueries(['entities']);
    }
  });

  // Offline sync integration
  const { queueOperation } = useOfflineSync();
  
  const handleSubmit = async (data: EntityData) => {
    if (navigator.onLine) {
      mutate(data);
    } else {
      await queueOperation('CREATE', '/api/v1/entities', data);
      toast({ title: "Saved Offline", description: "Will sync when connected" });
    }
  };

  return (
    // Component JSX here
  );
}
```

---

## Zimbabwe-Specific Implementation Notes

### **Payment Integration (Paynow)**
- Integration ID: [School-specific]
- Webhook URL: `https://api.1class.app/webhooks/paynow`
- Supported Methods: EcoCash, OneMoney, Zimswitch, Visa/Mastercard
- Currency: USD (primarily), ZWL (secondary)

### **Localization Requirements**
- **Primary**: English
- **Secondary**: Shona, Ndebele  
- **Number Format**: US format (1,234.56)
- **Date Format**: DD/MM/YYYY (Zimbabwe standard)
- **Phone Format**: +263 XX XXX XXXX

### **Compliance Requirements**
- **Data Protection**: Zimbabwe Cyber and Data Protection Act
- **Education**: Ministry of Primary and Secondary Education regulations
- **Financial**: Reserve Bank of Zimbabwe payment regulations

---

## Development Workflow

### **Git Branch Strategy**
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/module-X-component`: Feature branches
- `hotfix/`: Critical production fixes

### **Code Review Checklist**
- [ ] Multi-tenant data isolation enforced
- [ ] Offline sync implemented for user actions
- [ ] Zimbabwe-specific validations included
- [ ] Error handling with user-friendly messages
- [ ] Tests covering happy path and edge cases
- [ ] Performance optimized for 3G connections

### **Deployment Pipeline**
1. **Local Development**: Docker Compose
2. **Staging**: Railway deployment
3. **Production**: AWS EKS with auto-scaling
4. **Database**: AWS RDS PostgreSQL with read replicas

---

## Contact & Resources

### **Key Stakeholders**
- **Project Owner**: [Your Name]
- **Technical Lead**: Claude (AI Assistant)
- **Target Schools**: 3 pilot schools in Zimbabwe

### **External Resources**
- **Paynow API**: https://developers.paynow.co.zw/
- **ZIMSEC Syllabus**: Ministry portal access required
- **Zimbabwe Phone Validation**: +263 format standards

---

*This document is automatically updated at the end of each development session to maintain context continuity.*