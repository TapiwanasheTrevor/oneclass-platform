# OneClass Platform - Documentation Archiving System
**Version**: 1.0  
**Last Updated**: 2025-07-19  
**Purpose**: Maintain organized documentation throughout development lifecycle

---

## 🎯 **ARCHIVING PHILOSOPHY**

The OneClass platform maintains a **clean, organized documentation structure** that preserves important historical information while keeping the active workspace focused on current development priorities.

### **Active Documentation Principle**
- **Only 3 canonical documents** remain in active use at project root/docs level
- **All other documentation** is systematically archived with proper categorization
- **Module completion triggers** automatic archiving of implementation docs
- **Session handoffs** create permanent historical records

---

## 📁 **DIRECTORY STRUCTURE**

### **Active Documents (Never Archived)**
```
/oneclass_session_tracker.md          # Canonical session tracker (root level)
/docs/SESSION_HANDOFF_CURRENT.md      # Current project status
/docs/MODULE_DEVELOPMENT_SEQUENCE.md  # 39-module development roadmap
```

### **Archive Organization**
```
/docs/archive/
├── foundation-phase/              # Pre-module development docs
│   ├── DOCKER_TROUBLESHOOTING.md
│   ├── academic_module_prompt.md
│   └── [foundation implementation docs]
├── session-handoffs/              # Historical session documents
│   ├── SESSION_HANDOVER_AUTHENTICATION.md
│   ├── SESSION_HANDOVER_CLERK_INTEGRATION.md
│   ├── SESSION_HANDOVER_FINANCE.md
│   └── [date-stamped session handoffs]
├── module-implementations/        # Completed module documentation
│   ├── sis/                       # Student Information System
│   │   ├── api-reference.md       # API endpoints documentation
│   │   ├── database-schema.md     # Database models and relationships
│   │   ├── frontend-components.md # UI component specifications
│   │   └── implementation-notes.md # Development decisions and patterns
│   ├── academic/                  # Academic Management Module
│   └── [other completed modules]
├── archived-sessions/             # Development session logs
│   ├── 2025-07-19-foundation-complete.md
│   ├── 2025-07-20-sis-backend.md
│   └── [chronological session records]
└── deprecated/                    # Obsolete documentation
    ├── README_original.md
    └── [outdated implementation approaches]
```

---

## 🔄 **ARCHIVING WORKFLOWS**

### **During Module Development**
1. **Start of Module**: Create `/docs/archive/module-implementations/{module}/` directory
2. **During Development**: Document API endpoints, database changes, UI components
3. **Module Completion**: Move all module-specific docs to archive directory
4. **Update Canonical**: Reflect completion status in 3 canonical documents

### **Session-End Archiving**
```bash
# Example archiving workflow (end of session)
cd docs/archive/archived-sessions/
cp ../SESSION_HANDOFF_CURRENT.md $(date +%Y-%m-%d)-[module-name]-session.md
# Update canonical documents with new status
# Commit changes with descriptive message
```

### **Module Completion Archiving**
```bash
# When a module is 100% complete
cd docs/archive/module-implementations/
mkdir {module-name}/
# Move all module-specific documentation
mv ../../services/{module}/README.md {module-name}/api-reference.md
mv ../../database/schemas/{module}.sql.md {module-name}/database-schema.md
# Create implementation summary
echo "# {Module} Implementation Complete" > {module-name}/implementation-notes.md
```

---

## 📋 **DOCUMENTATION STANDARDS**

### **API Reference Documentation**
```markdown
# {Module} API Reference

## Endpoints
### POST /api/v1/{module}/{entity}
- **Purpose**: Create new {entity}
- **Authentication**: Required (JWT)
- **Permissions**: {required_roles}
- **Request Body**: {schema}
- **Response**: {response_schema}
- **Zimbabwe-Specific**: {local_requirements}

## Data Models
[SQLAlchemy models with field descriptions]

## Business Logic
[Key business rules and validation]
```

### **Database Schema Documentation**
```markdown
# {Module} Database Schema

## Tables
### {module}.{table_name}
- **Purpose**: {description}
- **Multi-tenancy**: Row Level Security enabled
- **Indexes**: {performance_indexes}
- **Relationships**: {foreign_keys}
- **Zimbabwe Fields**: {local_data_requirements}

## Migration History
[Chronological list of schema changes]
```

### **Frontend Component Documentation**
```markdown
# {Module} Frontend Components

## Component Hierarchy
{Module}Dashboard
├── {Entity}List
├── {Entity}Form
└── {Entity}Details

## User Journeys
[Step-by-step user workflows]

## Mobile Responsiveness
[Responsive design considerations]
```

---

## 🎯 **ARCHIVING TRIGGERS**

### **Automatic Archiving Events**
1. **Module 100% Complete**: All module docs → `/module-implementations/`
2. **Session End**: Current handoff → `/archived-sessions/`
3. **Phase Completion**: Phase-specific docs → appropriate archive folder
4. **Major Refactor**: Deprecated approaches → `/deprecated/`

### **Manual Archiving Events**
1. **Architecture Changes**: Old patterns moved to `/deprecated/`
2. **Tool Changes**: Old setup guides archived with date stamps
3. **Process Updates**: Previous workflows preserved for reference

---

## 🔍 **ARCHIVE SEARCH & RETRIEVAL**

### **Finding Archived Information**
```bash
# Search for specific module documentation
find docs/archive/module-implementations/ -name "*{keyword}*"

# Find session handoffs by date
ls docs/archive/archived-sessions/2025-07-*

# Search for API patterns across modules
grep -r "API endpoint" docs/archive/module-implementations/
```

### **Archive Index Maintenance**
Each archive subdirectory contains an `INDEX.md` file listing:
- All files in that directory
- Date archived
- Reason for archiving
- Cross-references to related documentation

---

## 📊 **ARCHIVE METRICS & MAINTENANCE**

### **Quarterly Archive Review**
- **Remove duplicates** and consolidate similar documents
- **Update cross-references** between archived and active docs
- **Verify completeness** of module implementation documentation
- **Clean up outdated** development session logs (>6 months old)

### **Archive Health Indicators**
- Each completed module has complete API, database, and frontend docs
- Session handoffs capture all major decisions and blockers
- No orphaned documentation without clear categorization
- Archive directory size remains manageable (<100MB)

---

## 🚀 **NEXT SESSION PREPARATION**

### **Pre-Session Archive Check**
Before starting any new development session:
1. **Verify canonical docs** are current and accurate
2. **Check if previous session** needs archiving
3. **Review relevant archived docs** for context
4. **Update wiki status** to reflect archive state

### **Wiki Integration**
The archive system integrates with `/docs/wiki/` structure:
- Wiki provides **high-level overviews** and navigation
- Archive provides **detailed implementation specifics**
- Cross-references maintain **bidirectional linking**

---

## 📞 **ARCHIVE ACCESS PATTERNS**

### **Common Archive Queries**
1. **"How did we implement authentication?"** → `/foundation-phase/`
2. **"What were the SIS API endpoints?"** → `/module-implementations/sis/`
3. **"Why did we change the database schema?"** → `/archived-sessions/`
4. **"What was the original architecture plan?"** → `/deprecated/`

### **Emergency Recovery**
If project context is lost:
1. Read all 3 canonical documents
2. Check latest archived session in `/archived-sessions/`
3. Review completed modules in `/module-implementations/`
4. Reconstruct current state from archive + git history

---

*This archiving system ensures that OneClass platform documentation remains organized, searchable, and valuable throughout the entire development lifecycle while maintaining focus on current priorities.*