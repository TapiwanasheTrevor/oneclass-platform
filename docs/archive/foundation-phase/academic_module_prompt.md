# Academic Management Module Implementation Prompt

## Module Overview
**Module Name:** Academic Management (Module 02)  
**Priority:** High  
**Dependencies:** SIS Module (Module 09) - Complete  
**Integration:** Finance Module (Module 10) - Complete  

## Project Context
The OneClass Platform is a comprehensive school management system designed specifically for Zimbabwe schools. We have successfully implemented the SIS (Student Information System) and Finance & Billing modules with full multitenancy, Zimbabwe-specific features, and comprehensive testing.

## Module 02 Requirements: Academic Management

### Core Features Required

#### 1. **Class Scheduling & Timetable Management**
- **Class Period Management**: Create and manage class periods with start/end times
- **Subject Timetables**: Build weekly/term timetables for each class
- **Teacher Assignments**: Assign teachers to subjects and classes
- **Room/Resource Allocation**: Manage classrooms and equipment scheduling
- **Conflict Detection**: Prevent scheduling conflicts for teachers and rooms
- **Zimbabwe School Calendar**: Support for 3-term academic year structure
- **Flexible Scheduling**: Support for double periods, practical sessions, and study periods

#### 2. **Attendance Tracking** (Extend existing SIS functionality)
- **Daily Attendance**: Mark student attendance for each class period
- **Bulk Attendance**: Quick attendance marking for entire classes
- **Attendance Reports**: Generate attendance reports by student, class, or date range
- **Absence Management**: Track excused/unexcused absences
- **Late Arrivals**: Track and manage student tardiness
- **Attendance Analytics**: Identify attendance patterns and trends
- **Parent Notifications**: Automated notifications for absences (integrate with Communication Hub)

#### 3. **Curriculum Management**
- **Curriculum Planning**: Create and manage curriculum for each grade level
- **Subject Definitions**: Define subjects with codes, descriptions, and grade levels
- **Learning Objectives**: Set and track learning objectives and outcomes
- **Curriculum Mapping**: Map curriculum to Zimbabwe Education standards
- **Progression Tracking**: Track student progress through curriculum
- **Resource Alignment**: Link curriculum to learning resources and materials

#### 4. **Assessment & Grading System**
- **Assessment Creation**: Create tests, quizzes, assignments, and projects
- **Grade Book Management**: Comprehensive grade book with multiple assessment types
- **Grading Scales**: Support Zimbabwe grading system (A-U grades)
- **Continuous Assessment**: Track ongoing assessments throughout the term
- **Performance Analytics**: Generate performance reports and analytics
- **Parent Access**: Allow parents to view student grades and progress
- **Grade Calculations**: Automated grade calculations with weighted categories

#### 5. **Lesson Planning & Management**
- **Lesson Plan Creation**: Create detailed lesson plans with objectives and activities
- **Resource Attachment**: Attach files, links, and materials to lessons
- **Curriculum Alignment**: Align lessons with curriculum standards
- **Lesson Scheduling**: Schedule lessons within the timetable
- **Collaboration Tools**: Share lesson plans with other teachers
- **Template Library**: Provide lesson plan templates for common subjects

#### 6. **Academic Calendar Management**
- **Term Planning**: Create and manage academic terms and holidays
- **Event Scheduling**: Schedule academic events, exams, and activities
- **Deadline Management**: Track assignment and assessment deadlines
- **Holiday Integration**: Integrate Zimbabwe public holidays
- **Calendar Sharing**: Share calendars with students and parents
- **Notification System**: Automated reminders for upcoming events

### Zimbabwe-Specific Requirements

#### 1. **Education System Compliance**
- **Grade Structure**: Support for Grade 1-7 (Primary) and Form 1-6 (Secondary)
- **Subject Codes**: Use Zimbabwe Education Ministry subject codes
- **Grading System**: Implement A, B, C, D, E, U grading scale
- **Curriculum Standards**: Align with Zimbabwe Curriculum Framework
- **Assessment Methods**: Support continuous assessment and final exams
- **Language Support**: English, Shona, and Ndebele language support

#### 2. **Local Academic Calendar**
- **Three-Term System**: Term 1 (Jan-Apr), Term 2 (May-Aug), Term 3 (Sep-Dec)
- **Public Holidays**: Zimbabwe public holidays and school holidays
- **Exam Periods**: National exam periods (Grade 7, Form 4, Form 6)
- **Sports Seasons**: Integration with local sports calendar
- **Cultural Events**: Include cultural and heritage events

#### 3. **Assessment Compliance**
- **Continuous Assessment**: 30% continuous, 70% final exam structure
- **Portfolio Assessment**: Support for practical subjects portfolio
- **Moderation Systems**: Grade moderation and quality assurance
- **External Exams**: Integration with ZIMSEC exam schedules
- **Progress Reports**: Zimbabwe-standard progress report formats

### Technical Requirements

#### 1. **Database Schema**
- **Multitenancy**: Full RLS (Row Level Security) for school isolation
- **Performance**: Optimized for large datasets (1000+ students per school)
- **Relationships**: Strong relationships with SIS and Finance modules
- **Audit Trails**: Complete audit trails for all academic records
- **Data Integrity**: Constraints and validations for academic data

#### 2. **API Requirements**
- **RESTful Design**: Consistent with existing SIS and Finance APIs
- **Authentication**: JWT-based authentication with role-based access
- **Rate Limiting**: Prevent abuse and ensure fair usage
- **Caching**: Implement caching for frequently accessed data
- **Documentation**: OpenAPI 3.0 documentation for all endpoints

#### 3. **Frontend Requirements**
- **Responsive Design**: Mobile-first design using Tailwind CSS
- **Component Library**: Use shadcn/ui components for consistency
- **Real-time Updates**: WebSocket support for live updates
- **Offline Support**: Basic offline functionality for critical features
- **Performance**: Fast loading and smooth interactions

### Integration Requirements

#### 1. **SIS Module Integration**
- **Student Data**: Seamless access to student information
- **Class Enrollment**: Use existing class enrollment data
- **Guardian Information**: Access guardian data for communications
- **Academic History**: Build upon existing academic records

#### 2. **Finance Module Integration**
- **Fee-based Access**: Link subject access to fee payments
- **Resource Billing**: Integrate with equipment and resource fees
- **Payment Status**: Consider payment status for access to materials
- **Financial Reports**: Include academic data in financial analytics

#### 3. **Future Module Integration**
- **Communication Hub**: Ready for parent-teacher communication
- **Resource Management**: Prepared for library and equipment modules
- **Analytics Dashboard**: Export data for advanced analytics
- **Mobile App**: API-ready for mobile applications

### Quality Standards

#### 1. **Code Quality**
- **TypeScript**: Strict TypeScript for frontend components
- **Python Standards**: Follow PEP 8 and use type hints
- **Testing**: Minimum 80% test coverage
- **Documentation**: Comprehensive inline documentation
- **Code Reviews**: All code must be reviewed before merge

#### 2. **Security Standards**
- **Data Protection**: Encrypt sensitive academic data
- **Access Control**: Role-based access for different user types
- **Audit Logging**: Log all academic record changes
- **Privacy Compliance**: Ensure student data privacy
- **Backup Systems**: Regular backups of academic data

#### 3. **Performance Standards**
- **Response Times**: API responses under 200ms for simple queries
- **Scalability**: Support for 10,000+ students per school
- **Database Optimization**: Efficient queries and indexing
- **Caching Strategy**: Implement multi-layer caching
- **Load Testing**: Verify performance under load

### Implementation Phases

#### Phase 1: Foundation (High Priority)
1. **Database Schema**: Complete academic management schema
2. **Class Scheduling**: Basic timetable management
3. **Attendance System**: Enhanced attendance tracking
4. **Basic Assessment**: Simple grade book functionality

#### Phase 2: Core Features (High Priority)
1. **Curriculum Management**: Full curriculum planning
2. **Advanced Assessment**: Comprehensive assessment system
3. **Lesson Planning**: Complete lesson planning tools
4. **Academic Calendar**: Full calendar management

#### Phase 3: Advanced Features (Medium Priority)
1. **Analytics Dashboard**: Performance analytics and reporting
2. **Parent Portal**: Parent access to academic information
3. **Mobile Optimization**: Mobile-specific features
4. **Integration APIs**: External system integrations

#### Phase 4: Optimization (Low Priority)
1. **Performance Tuning**: Optimize for large-scale usage
2. **Advanced Reporting**: Custom report generation
3. **AI Features**: Predictive analytics and insights
4. **Third-party Integration**: LMS and other system integration

### Success Metrics

#### 1. **Functional Metrics**
- **Feature Completeness**: 100% of core features implemented
- **Data Accuracy**: 99.9% accuracy in academic records
- **User Adoption**: 90% active usage within 3 months
- **Performance**: Sub-200ms response times for 95% of requests

#### 2. **Quality Metrics**
- **Test Coverage**: Minimum 80% code coverage
- **Bug Reports**: Less than 5 critical bugs per month
- **Security**: Zero security vulnerabilities
- **Documentation**: 100% API documentation coverage

#### 3. **User Experience Metrics**
- **User Satisfaction**: 4.5+ rating from teachers and administrators
- **Training Time**: Less than 2 hours for new user onboarding
- **Error Rates**: Less than 1% user-reported errors
- **Support Tickets**: Less than 10 support tickets per 100 users per month

### Deliverables

#### 1. **Database Layer**
- Complete academic management schema (02_academic.sql)
- Migration scripts and seed data
- Performance optimization and indexing
- RLS policies and security constraints

#### 2. **Backend Services**
- FastAPI service with all endpoints
- Comprehensive CRUD operations
- Business logic and validation
- Integration with existing modules

#### 3. **Frontend Components**
- React components for all features
- Form handling and validation
- Real-time updates and notifications
- Mobile-responsive design

#### 4. **Testing Suite**
- Unit tests for all components
- Integration tests for API endpoints
- End-to-end tests for user workflows
- Performance and security tests

#### 5. **Documentation**
- Technical documentation
- User guides and tutorials
- API documentation
- Deployment guides

### Technical Specifications

#### 1. **Database Tables Required**
- `academic.subjects` - Subject definitions and codes
- `academic.curricula` - Curriculum structures
- `academic.timetables` - Class scheduling
- `academic.periods` - Class periods and timing
- `academic.assessments` - Assessment definitions
- `academic.grades` - Grade records
- `academic.lesson_plans` - Lesson planning
- `academic.attendance_sessions` - Attendance tracking
- `academic.academic_calendar` - Calendar events

#### 2. **API Endpoints Required**
- `/api/v1/academic/subjects` - Subject management
- `/api/v1/academic/timetables` - Timetable management
- `/api/v1/academic/attendance` - Attendance tracking
- `/api/v1/academic/assessments` - Assessment management
- `/api/v1/academic/grades` - Grade management
- `/api/v1/academic/lesson-plans` - Lesson planning
- `/api/v1/academic/calendar` - Calendar management
- `/api/v1/academic/reports` - Academic reporting

#### 3. **Frontend Components Required**
- `TimetableManagement` - Timetable creation and editing
- `AttendanceTracker` - Attendance marking interface
- `GradeBook` - Grade entry and management
- `LessonPlanner` - Lesson plan creation
- `CurriculumManager` - Curriculum planning
- `AcademicCalendar` - Calendar management
- `AssessmentCreator` - Assessment creation
- `ReportGenerator` - Academic report generation

### Next Steps

1. **Create Database Schema** - Start with academic management schema
2. **Implement Backend Services** - Build FastAPI services
3. **Create Frontend Components** - Build React components
4. **Integration Testing** - Test with existing modules
5. **User Acceptance Testing** - Test with real users
6. **Production Deployment** - Deploy to production environment

This comprehensive Academic Management module will provide Zimbabwe schools with a complete solution for managing their academic operations, building upon the strong foundation of the SIS and Finance modules already implemented.