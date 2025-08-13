-- =====================================================
-- OneClass Academic Management Module - Zimbabwe Seed Data
-- Populate Zimbabwe Education System Base Data
-- =====================================================

-- Migration: 002_seed_zimbabwe_data
-- Description: Insert Zimbabwe-specific academic data including subjects, periods, and reference data
-- Date: 2025-08-13
-- Author: OneClass Development Team

BEGIN;

-- =====================================================
-- ZIMBABWE CORE SUBJECTS SEED DATA
-- =====================================================

-- Insert core Primary School subjects (Grades 1-7)
INSERT INTO academic.subjects (
    id, school_id, code, name, description, grade_levels, is_core, is_practical, 
    requires_lab, pass_mark, max_mark, credit_hours, department, language_of_instruction, display_order
) VALUES 
-- Primary School Core Subjects
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'ENG', 'English Language', 'English Language and Literature', ARRAY[1,2,3,4,5,6,7], true, false, false, 50.00, 100.00, 5, 'Languages', 'English', 1),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'SHO', 'Shona', 'Shona Language and Literature', ARRAY[1,2,3,4,5,6,7], true, false, false, 50.00, 100.00, 4, 'Languages', 'Shona', 2),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'NDE', 'Ndebele', 'Ndebele Language and Literature', ARRAY[1,2,3,4,5,6,7], true, false, false, 50.00, 100.00, 4, 'Languages', 'Ndebele', 3),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'MATH', 'Mathematics', 'Primary Mathematics', ARRAY[1,2,3,4,5,6,7], true, false, false, 50.00, 100.00, 5, 'Mathematics', 'English', 4),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'SCI', 'General Science', 'Primary Science', ARRAY[1,2,3,4,5,6,7], true, true, false, 50.00, 100.00, 4, 'Science', 'English', 5),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'SST', 'Social Studies', 'Social Studies and History', ARRAY[1,2,3,4,5,6,7], true, false, false, 50.00, 100.00, 3, 'Social Studies', 'English', 6),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'RME', 'Religious & Moral Education', 'Religious and Moral Education', ARRAY[1,2,3,4,5,6,7], true, false, false, 50.00, 100.00, 2, 'Religious Studies', 'English', 7),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'PE', 'Physical Education', 'Physical Education and Sports', ARRAY[1,2,3,4,5,6,7], false, true, false, 50.00, 100.00, 2, 'Sports', 'English', 8),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'ART', 'Art & Crafts', 'Visual Arts and Crafts', ARRAY[1,2,3,4,5,6,7], false, true, false, 50.00, 100.00, 2, 'Arts', 'English', 9),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'MUS', 'Music', 'Music Education', ARRAY[1,2,3,4,5,6,7], false, true, false, 50.00, 100.00, 2, 'Arts', 'English', 10),

-- Secondary School Core Subjects (Forms 1-6)
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'ENGL', 'English Language', 'O/A Level English Language', ARRAY[8,9,10,11,12,13], true, false, false, 50.00, 100.00, 5, 'Languages', 'English', 11),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'ENGLIT', 'English Literature', 'English Literature in English', ARRAY[8,9,10,11,12,13], false, false, false, 50.00, 100.00, 4, 'Languages', 'English', 12),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'SHOL', 'Shona Language', 'O/A Level Shona', ARRAY[8,9,10,11,12,13], true, false, false, 50.00, 100.00, 4, 'Languages', 'Shona', 13),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'NDEL', 'Ndebele Language', 'O/A Level Ndebele', ARRAY[8,9,10,11,12,13], true, false, false, 50.00, 100.00, 4, 'Languages', 'Ndebele', 14),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'MATHS', 'Mathematics', 'O/A Level Mathematics', ARRAY[8,9,10,11,12,13], true, false, false, 50.00, 100.00, 6, 'Mathematics', 'English', 15),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'AMATHS', 'Additional Mathematics', 'Additional Mathematics', ARRAY[10,11,12,13], false, false, false, 50.00, 100.00, 5, 'Mathematics', 'English', 16),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'PHYS', 'Physics', 'O/A Level Physics', ARRAY[8,9,10,11,12,13], false, true, true, 50.00, 100.00, 5, 'Science', 'English', 17),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'CHEM', 'Chemistry', 'O/A Level Chemistry', ARRAY[8,9,10,11,12,13], false, true, true, 50.00, 100.00, 5, 'Science', 'English', 18),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'BIO', 'Biology', 'O/A Level Biology', ARRAY[8,9,10,11,12,13], false, true, true, 50.00, 100.00, 5, 'Science', 'English', 19),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'INTSC', 'Integrated Science', 'Integrated Science', ARRAY[8,9], true, true, true, 50.00, 100.00, 5, 'Science', 'English', 20),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'HIST', 'History', 'History', ARRAY[8,9,10,11,12,13], false, false, false, 50.00, 100.00, 4, 'Social Studies', 'English', 21),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'GEOG', 'Geography', 'Geography', ARRAY[8,9,10,11,12,13], false, true, false, 50.00, 100.00, 4, 'Social Studies', 'English', 22),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'RE', 'Religious Education', 'Religious Education', ARRAY[8,9,10,11], false, false, false, 50.00, 100.00, 3, 'Religious Studies', 'English', 23),

-- Commercial Subjects
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'ACC', 'Accounts', 'Principles of Accounts', ARRAY[8,9,10,11,12,13], false, false, false, 50.00, 100.00, 5, 'Commerce', 'English', 24),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'BSTD', 'Business Studies', 'Business Studies & Enterprise', ARRAY[8,9,10,11,12,13], false, false, false, 50.00, 100.00, 4, 'Commerce', 'English', 25),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'ECON', 'Economics', 'Economics', ARRAY[8,9,10,11,12,13], false, false, false, 50.00, 100.00, 4, 'Commerce', 'English', 26),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'COMP', 'Computer Studies', 'Computer Studies & ICT', ARRAY[8,9,10,11,12,13], false, true, true, 50.00, 100.00, 4, 'Technology', 'English', 27),

-- Technical Subjects
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'BST', 'Building Studies', 'Building Studies & Technology', ARRAY[8,9,10,11], false, true, false, 50.00, 100.00, 5, 'Technology', 'English', 28),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'EGS', 'Engineering Science', 'Engineering Science', ARRAY[8,9,10,11], false, true, true, 50.00, 100.00, 5, 'Technology', 'English', 29),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'TECH', 'Technical Graphics', 'Technical Graphics & Design', ARRAY[8,9,10,11], false, true, false, 50.00, 100.00, 4, 'Technology', 'English', 30),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'WOOD', 'Woodwork', 'Woodwork Technology', ARRAY[8,9,10,11], false, true, true, 50.00, 100.00, 4, 'Technology', 'English', 31),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'METAL', 'Metalwork', 'Metalwork Technology', ARRAY[8,9,10,11], false, true, true, 50.00, 100.00, 4, 'Technology', 'English', 32),

-- Home Economics
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'HOME', 'Home Economics', 'Home Economics & Nutrition', ARRAY[8,9,10,11], false, true, false, 50.00, 100.00, 4, 'Home Economics', 'English', 33),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'FOOD', 'Food & Nutrition', 'Food Science & Nutrition', ARRAY[8,9,10,11,12,13], false, true, true, 50.00, 100.00, 4, 'Home Economics', 'English', 34),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'FASH', 'Fashion & Fabrics', 'Fashion Design & Textiles', ARRAY[8,9,10,11,12,13], false, true, false, 50.00, 100.00, 4, 'Home Economics', 'English', 35),

-- Arts Subjects
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'ARTS', 'Art', 'Visual Arts & Design', ARRAY[8,9,10,11,12,13], false, true, false, 50.00, 100.00, 4, 'Arts', 'English', 36),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'MUSIC', 'Music', 'Music Theory & Practice', ARRAY[8,9,10,11,12,13], false, true, false, 50.00, 100.00, 4, 'Arts', 'English', 37),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'DRAMA', 'Drama', 'Theatre Arts & Drama', ARRAY[8,9,10,11], false, true, false, 50.00, 100.00, 3, 'Arts', 'English', 38),

-- Languages
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'FREN', 'French', 'French Language', ARRAY[8,9,10,11,12,13], false, false, false, 50.00, 100.00, 4, 'Languages', 'French', 39),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'PORT', 'Portuguese', 'Portuguese Language', ARRAY[8,9,10,11,12,13], false, false, false, 50.00, 100.00, 4, 'Languages', 'Portuguese', 40),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'ARAB', 'Arabic', 'Arabic Language', ARRAY[8,9,10,11], false, false, false, 50.00, 100.00, 3, 'Languages', 'Arabic', 41),

-- A-Level Specific Subjects
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'DIVS', 'Divinity', 'Religious Studies/Divinity', ARRAY[12,13], false, false, false, 50.00, 100.00, 4, 'Religious Studies', 'English', 42),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'LAW', 'Law', 'Legal Studies', ARRAY[12,13], false, false, false, 50.00, 100.00, 4, 'Social Studies', 'English', 43),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'SOC', 'Sociology', 'Sociology', ARRAY[12,13], false, false, false, 50.00, 100.00, 4, 'Social Studies', 'English', 44),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 'PHIL', 'Philosophy', 'Philosophy', ARRAY[12,13], false, false, false, 50.00, 100.00, 4, 'Social Studies', 'English', 45)

ON CONFLICT (school_id, code) DO NOTHING;

-- =====================================================
-- STANDARD SCHOOL PERIODS SEED DATA
-- =====================================================

-- Insert typical Zimbabwe school periods
INSERT INTO academic.periods (
    id, school_id, period_number, name, start_time, end_time, is_break, break_type
) VALUES 
-- School periods for a typical Zimbabwe secondary school
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 1, 'Period 1', '07:30:00', '08:10:00', false, null),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 2, 'Period 2', '08:10:00', '08:50:00', false, null),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 3, 'Tea Break', '08:50:00', '09:10:00', true, 'tea'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 4, 'Period 3', '09:10:00', '09:50:00', false, null),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 5, 'Period 4', '09:50:00', '10:30:00', false, null),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 6, 'Period 5', '10:30:00', '11:10:00', false, null),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 7, 'Period 6', '11:10:00', '11:50:00', false, null),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 8, 'Lunch Break', '11:50:00', '12:50:00', true, 'lunch'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 9, 'Period 7', '12:50:00', '13:30:00', false, null),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 10, 'Period 8', '13:30:00', '14:10:00', false, null),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 11, 'Period 9', '14:10:00', '14:50:00', false, null),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 12, 'Period 10', '14:50:00', '15:30:00', false, null),

-- Primary school periods (shorter)
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 13, 'Assembly', '07:30:00', '08:00:00', true, 'assembly'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 14, 'Lesson 1', '08:00:00', '08:30:00', false, null),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 15, 'Lesson 2', '08:30:00', '09:00:00', false, null),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 16, 'Break', '09:00:00', '09:15:00', true, 'tea'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 17, 'Lesson 3', '09:15:00', '09:45:00', false, null),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 18, 'Lesson 4', '09:45:00', '10:15:00', false, null),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 19, 'Lesson 5', '10:15:00', '10:45:00', false, null),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 20, 'Lesson 6', '10:45:00', '11:15:00', false, null),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 21, 'Lunch', '11:15:00', '12:00:00', true, 'lunch'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 22, 'Lesson 7', '12:00:00', '12:30:00', false, null),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', 23, 'Lesson 8', '12:30:00', '13:00:00', false, null)

ON CONFLICT (school_id, period_number) DO NOTHING;

-- =====================================================
-- ZIMBABWE CALENDAR EVENTS SEED DATA
-- =====================================================

-- Insert common Zimbabwe education calendar events
INSERT INTO academic.calendar_events (
    id, school_id, academic_year_id, title, description, event_type, event_category,
    start_date, end_date, is_all_day, term_number, is_public, status
) VALUES 
-- Term 1 Events
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Term 1 Opening', 'First term opening day', 'academic', 'academic', '2025-01-15', '2025-01-15', true, 1, true, 'scheduled'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Term 1 Mid-Term Assessments', 'Mid-term continuous assessments', 'assessment', 'academic', '2025-02-17', '2025-02-21', true, 1, false, 'scheduled'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Term 1 Examinations', 'End of term examinations', 'exam', 'academic', '2025-04-07', '2025-04-18', true, 1, false, 'scheduled'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Term 1 Closing', 'First term closing day', 'academic', 'academic', '2025-04-18', '2025-04-18', true, 1, true, 'scheduled'),

-- Term 2 Events
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Term 2 Opening', 'Second term opening day', 'academic', 'academic', '2025-05-06', '2025-05-06', true, 2, true, 'scheduled'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Independence Day', 'Zimbabwe Independence Day Holiday', 'holiday', 'cultural', '2025-04-18', '2025-04-18', true, null, true, 'scheduled'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Workers Day', 'International Workers Day Holiday', 'holiday', 'cultural', '2025-05-01', '2025-05-01', true, null, true, 'scheduled'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Term 2 Mid-Term Assessments', 'Mid-term continuous assessments', 'assessment', 'academic', '2025-06-16', '2025-06-20', true, 2, false, 'scheduled'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Term 2 Examinations', 'End of term examinations', 'exam', 'academic', '2025-08-11', '2025-08-22', true, 2, false, 'scheduled'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Term 2 Closing', 'Second term closing day', 'academic', 'academic', '2025-08-22', '2025-08-22', true, 2, true, 'scheduled'),

-- Term 3 Events
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Term 3 Opening', 'Third term opening day', 'academic', 'academic', '2025-09-09', '2025-09-09', true, 3, true, 'scheduled'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Heroes Day', 'National Heroes Day Holiday', 'holiday', 'cultural', '2025-08-11', '2025-08-11', true, null, true, 'scheduled'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Defence Forces Day', 'Zimbabwe Defence Forces Day', 'holiday', 'cultural', '2025-08-12', '2025-08-12', true, null, true, 'scheduled'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Term 3 Mid-Term Assessments', 'Mid-term continuous assessments', 'assessment', 'academic', '2025-10-20', '2025-10-24', true, 3, false, 'scheduled'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Annual Sports Day', 'School sports and athletics day', 'sports', 'sports', '2025-10-10', '2025-10-10', true, 3, true, 'scheduled'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Prize Giving Day', 'Annual prize giving ceremony', 'cultural', 'social', '2025-11-15', '2025-11-15', true, 3, true, 'scheduled'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Final Examinations', 'End of year final examinations', 'exam', 'academic', '2025-11-24', '2025-12-05', true, 3, false, 'scheduled'),
(uuid_generate_v4(), '00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'Term 3 Closing', 'Third term and year closing', 'academic', 'academic', '2025-12-05', '2025-12-05', true, 3, true, 'scheduled')

ON CONFLICT DO NOTHING;

-- =====================================================
-- UPDATE STATISTICS AND OPTIMIZE
-- =====================================================

-- Update table statistics for query optimization
ANALYZE academic.subjects;
ANALYZE academic.periods;
ANALYZE academic.calendar_events;

COMMIT;

-- =====================================================
-- ZIMBABWE SEED DATA COMPLETE
-- =====================================================
-- Zimbabwe Education System Compliance:
-- ✅ 45 Standard subjects (Primary & Secondary)
-- ✅ Complete grade level coverage (Grades 1-7, Forms 1-6)
-- ✅ Language support (English, Shona, Ndebele)
-- ✅ Core/Optional subject classification
-- ✅ Practical subjects with lab requirements
-- ✅ Standard school periods (Primary & Secondary)
-- ✅ Three-term academic calendar
-- ✅ Zimbabwe national holidays
-- ✅ ZIMSEC examination periods
-- ✅ Cultural and sports events
-- =====================================================