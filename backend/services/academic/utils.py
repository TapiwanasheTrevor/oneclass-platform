"""
Academic Management Utility Functions
Helper functions for academic management operations
"""

from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from .schemas import GradingScale, TermNumber, AttendanceStatus, AssessmentType

# =====================================================
# GRADING UTILITIES
# =====================================================

def get_zimbabwe_grade(percentage: float) -> GradingScale:
    """Convert percentage to Zimbabwe grading scale"""
    if percentage >= 80:
        return GradingScale.A
    elif percentage >= 70:
        return GradingScale.B
    elif percentage >= 60:
        return GradingScale.C
    elif percentage >= 50:
        return GradingScale.D
    elif percentage >= 40:
        return GradingScale.E
    else:
        return GradingScale.U


def calculate_grade_points(letter_grade: GradingScale) -> Decimal:
    """Calculate grade points from letter grade"""
    grade_points_map = {
        GradingScale.A: Decimal('4.0'),
        GradingScale.B: Decimal('3.0'),
        GradingScale.C: Decimal('2.0'),
        GradingScale.D: Decimal('1.0'),
        GradingScale.E: Decimal('0.5'),
        GradingScale.U: Decimal('0.0')
    }
    return grade_points_map.get(letter_grade, Decimal('0.0'))


def calculate_weighted_average(grades: List[Dict[str, Any]]) -> Decimal:
    """Calculate weighted average from a list of grades with weights"""
    if not grades:
        return Decimal('0.0')
    
    total_weighted_score = Decimal('0.0')
    total_weight = Decimal('0.0')
    
    for grade in grades:
        if grade.get('percentage_score') is not None and grade.get('weight_percentage') is not None:
            score = Decimal(str(grade['percentage_score']))
            weight = Decimal(str(grade['weight_percentage']))
            total_weighted_score += score * weight
            total_weight += weight
    
    if total_weight == 0:
        return Decimal('0.0')
    
    return (total_weighted_score / total_weight).quantize(Decimal('0.01'))


def get_grade_distribution(grades: List[Dict[str, Any]]) -> Dict[str, int]:
    """Get grade distribution statistics"""
    distribution = {grade.value: 0 for grade in GradingScale}
    
    for grade in grades:
        letter_grade = grade.get('letter_grade')
        if letter_grade and letter_grade in distribution:
            distribution[letter_grade] += 1
    
    return distribution


def calculate_pass_rate(grades: List[Dict[str, Any]], pass_grade: GradingScale = GradingScale.D) -> Decimal:
    """Calculate pass rate based on minimum passing grade"""
    if not grades:
        return Decimal('0.0')
    
    passing_grades = [GradingScale.A, GradingScale.B, GradingScale.C, GradingScale.D]
    if pass_grade == GradingScale.C:
        passing_grades = [GradingScale.A, GradingScale.B, GradingScale.C]
    elif pass_grade == GradingScale.B:
        passing_grades = [GradingScale.A, GradingScale.B]
    elif pass_grade == GradingScale.A:
        passing_grades = [GradingScale.A]
    
    passed_count = sum(1 for grade in grades 
                      if grade.get('letter_grade') in [g.value for g in passing_grades])
    
    return (Decimal(passed_count) / Decimal(len(grades)) * 100).quantize(Decimal('0.01'))


# =====================================================
# ATTENDANCE UTILITIES
# =====================================================

def calculate_attendance_rate(attendance_records: List[Dict[str, Any]]) -> Decimal:
    """Calculate attendance rate from attendance records"""
    if not attendance_records:
        return Decimal('0.0')
    
    present_count = sum(1 for record in attendance_records 
                       if record.get('attendance_status') in [AttendanceStatus.PRESENT.value, AttendanceStatus.LATE.value])
    
    return (Decimal(present_count) / Decimal(len(attendance_records)) * 100).quantize(Decimal('0.01'))


def get_attendance_trend(attendance_records: List[Dict[str, Any]], period_days: int = 30) -> List[Dict[str, Any]]:
    """Get attendance trend over a specified period"""
    if not attendance_records:
        return []
    
    # Group by date
    date_attendance = {}
    for record in attendance_records:
        session_date = record.get('session_date')
        if session_date:
            if session_date not in date_attendance:
                date_attendance[session_date] = {'present': 0, 'absent': 0, 'late': 0, 'total': 0}
            
            status = record.get('attendance_status')
            if status == AttendanceStatus.PRESENT.value:
                date_attendance[session_date]['present'] += 1
            elif status == AttendanceStatus.ABSENT.value:
                date_attendance[session_date]['absent'] += 1
            elif status == AttendanceStatus.LATE.value:
                date_attendance[session_date]['late'] += 1
            
            date_attendance[session_date]['total'] += 1
    
    # Calculate daily rates
    trend = []
    for date_str, counts in sorted(date_attendance.items()):
        if counts['total'] > 0:
            rate = (counts['present'] + counts['late']) / counts['total'] * 100
            trend.append({
                'date': date_str,
                'attendance_rate': round(rate, 2),
                'present': counts['present'],
                'absent': counts['absent'],
                'late': counts['late'],
                'total': counts['total']
            })
    
    return trend[-period_days:] if len(trend) > period_days else trend


def identify_chronic_absentees(attendance_records: List[Dict[str, Any]], threshold: float = 80.0) -> List[UUID]:
    """Identify students with chronic absenteeism"""
    student_attendance = {}
    
    for record in attendance_records:
        student_id = record.get('student_id')
        if student_id:
            if student_id not in student_attendance:
                student_attendance[student_id] = {'present': 0, 'total': 0}
            
            student_attendance[student_id]['total'] += 1
            if record.get('attendance_status') in [AttendanceStatus.PRESENT.value, AttendanceStatus.LATE.value]:
                student_attendance[student_id]['present'] += 1
    
    chronic_absentees = []
    for student_id, counts in student_attendance.items():
        if counts['total'] > 0:
            rate = (counts['present'] / counts['total']) * 100
            if rate < threshold:
                chronic_absentees.append(student_id)
    
    return chronic_absentees


# =====================================================
# ASSESSMENT UTILITIES
# =====================================================

def categorize_assessment_performance(percentage: float) -> str:
    """Categorize assessment performance level"""
    if percentage >= 80:
        return "Excellent"
    elif percentage >= 70:
        return "Good"
    elif percentage >= 60:
        return "Satisfactory"
    elif percentage >= 50:
        return "Needs Improvement"
    elif percentage >= 40:
        return "Below Average"
    else:
        return "Poor"


def calculate_assessment_statistics(grades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate comprehensive assessment statistics"""
    if not grades:
        return {
            'total_students': 0,
            'average_score': 0.0,
            'highest_score': 0.0,
            'lowest_score': 0.0,
            'median_score': 0.0,
            'pass_rate': 0.0,
            'grade_distribution': {},
            'performance_categories': {}
        }
    
    scores = [float(grade['percentage_score']) for grade in grades 
              if grade.get('percentage_score') is not None]
    
    if not scores:
        return {
            'total_students': len(grades),
            'average_score': 0.0,
            'highest_score': 0.0,
            'lowest_score': 0.0,
            'median_score': 0.0,
            'pass_rate': 0.0,
            'grade_distribution': {},
            'performance_categories': {}
        }
    
    # Basic statistics
    scores.sort()
    total_students = len(grades)
    average_score = sum(scores) / len(scores)
    highest_score = max(scores)
    lowest_score = min(scores)
    median_score = scores[len(scores) // 2] if len(scores) % 2 == 1 else (scores[len(scores) // 2 - 1] + scores[len(scores) // 2]) / 2
    
    # Grade distribution
    grade_distribution = get_grade_distribution(grades)
    
    # Performance categories
    performance_categories = {
        'Excellent': 0,
        'Good': 0,
        'Satisfactory': 0,
        'Needs Improvement': 0,
        'Below Average': 0,
        'Poor': 0
    }
    
    for score in scores:
        category = categorize_assessment_performance(score)
        performance_categories[category] += 1
    
    # Pass rate (assuming 50% is passing)
    pass_rate = calculate_pass_rate(grades)
    
    return {
        'total_students': total_students,
        'average_score': round(average_score, 2),
        'highest_score': round(highest_score, 2),
        'lowest_score': round(lowest_score, 2),
        'median_score': round(median_score, 2),
        'pass_rate': float(pass_rate),
        'grade_distribution': grade_distribution,
        'performance_categories': performance_categories
    }


def generate_assessment_insights(statistics: Dict[str, Any]) -> List[str]:
    """Generate insights from assessment statistics"""
    insights = []
    
    avg_score = statistics.get('average_score', 0)
    pass_rate = statistics.get('pass_rate', 0)
    grade_dist = statistics.get('grade_distribution', {})
    
    # Average score insights
    if avg_score >= 80:
        insights.append("Excellent class performance with high average score")
    elif avg_score >= 70:
        insights.append("Good class performance overall")
    elif avg_score >= 60:
        insights.append("Satisfactory class performance")
    elif avg_score >= 50:
        insights.append("Class performance needs improvement")
    else:
        insights.append("Poor class performance requires immediate attention")
    
    # Pass rate insights
    if pass_rate >= 90:
        insights.append("Excellent pass rate - most students mastered the content")
    elif pass_rate >= 80:
        insights.append("Good pass rate with room for improvement")
    elif pass_rate >= 70:
        insights.append("Moderate pass rate - consider additional support")
    elif pass_rate >= 60:
        insights.append("Low pass rate - review teaching methods")
    else:
        insights.append("Very low pass rate - immediate intervention required")
    
    # Grade distribution insights
    if grade_dist.get('A', 0) > grade_dist.get('U', 0):
        insights.append("More students achieving top grades than failing")
    elif grade_dist.get('U', 0) > grade_dist.get('A', 0):
        insights.append("High number of failing students requires attention")
    
    return insights


# =====================================================
# TIMETABLE UTILITIES
# =====================================================

def validate_timetable_slot(
    day_of_week: int,
    period_start: time,
    period_end: time,
    existing_timetables: List[Dict[str, Any]]
) -> Tuple[bool, str]:
    """Validate if a timetable slot is available"""
    for existing in existing_timetables:
        if existing.get('day_of_week') == day_of_week:
            existing_start = existing.get('start_time')
            existing_end = existing.get('end_time')
            
            if existing_start and existing_end:
                # Check for time overlap
                if (period_start < existing_end and period_end > existing_start):
                    return False, f"Time slot conflicts with existing class at {existing_start}-{existing_end}"
    
    return True, "Slot is available"


def generate_timetable_conflicts(timetables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate list of timetable conflicts"""
    conflicts = []
    
    for i, timetable1 in enumerate(timetables):
        for j, timetable2 in enumerate(timetables[i + 1:], i + 1):
            if (timetable1.get('day_of_week') == timetable2.get('day_of_week') and
                timetable1.get('period_id') == timetable2.get('period_id')):
                
                # Check for teacher conflicts
                if timetable1.get('teacher_id') == timetable2.get('teacher_id'):
                    conflicts.append({
                        'type': 'teacher_conflict',
                        'teacher_id': timetable1.get('teacher_id'),
                        'day_of_week': timetable1.get('day_of_week'),
                        'period_id': timetable1.get('period_id'),
                        'classes': [timetable1.get('class_id'), timetable2.get('class_id')]
                    })
                
                # Check for classroom conflicts
                if (timetable1.get('room_number') and 
                    timetable2.get('room_number') and
                    timetable1.get('room_number') == timetable2.get('room_number')):
                    conflicts.append({
                        'type': 'room_conflict',
                        'room_number': timetable1.get('room_number'),
                        'day_of_week': timetable1.get('day_of_week'),
                        'period_id': timetable1.get('period_id'),
                        'classes': [timetable1.get('class_id'), timetable2.get('class_id')]
                    })
    
    return conflicts


def calculate_teacher_workload(timetables: List[Dict[str, Any]], teacher_id: UUID) -> Dict[str, Any]:
    """Calculate teacher workload statistics"""
    teacher_timetables = [t for t in timetables if t.get('teacher_id') == teacher_id]
    
    if not teacher_timetables:
        return {
            'total_periods': 0,
            'unique_subjects': 0,
            'unique_classes': 0,
            'daily_breakdown': {},
            'subject_breakdown': {}
        }
    
    # Daily breakdown
    daily_breakdown = {}
    for timetable in teacher_timetables:
        day = timetable.get('day_of_week')
        if day not in daily_breakdown:
            daily_breakdown[day] = 0
        daily_breakdown[day] += 1
    
    # Subject breakdown
    subject_breakdown = {}
    for timetable in teacher_timetables:
        subject_id = timetable.get('subject_id')
        if subject_id not in subject_breakdown:
            subject_breakdown[subject_id] = 0
        subject_breakdown[subject_id] += 1
    
    return {
        'total_periods': len(teacher_timetables),
        'unique_subjects': len(set(t.get('subject_id') for t in teacher_timetables)),
        'unique_classes': len(set(t.get('class_id') for t in teacher_timetables)),
        'daily_breakdown': daily_breakdown,
        'subject_breakdown': subject_breakdown
    }


# =====================================================
# CALENDAR UTILITIES
# =====================================================

def get_zimbabwe_public_holidays(year: int) -> List[Dict[str, Any]]:
    """Get Zimbabwe public holidays for a given year"""
    holidays = [
        {'date': f'{year}-01-01', 'name': 'New Year\'s Day', 'type': 'public'},
        {'date': f'{year}-04-18', 'name': 'Independence Day', 'type': 'public'},
        {'date': f'{year}-05-01', 'name': 'Workers\' Day', 'type': 'public'},
        {'date': f'{year}-08-11', 'name': 'Heroes\' Day', 'type': 'public'},
        {'date': f'{year}-08-12', 'name': 'Defence Forces Day', 'type': 'public'},
        {'date': f'{year}-12-22', 'name': 'Unity Day', 'type': 'public'},
        {'date': f'{year}-12-25', 'name': 'Christmas Day', 'type': 'public'},
        {'date': f'{year}-12-26', 'name': 'Boxing Day', 'type': 'public'},
    ]
    
    return holidays


def get_zimbabwe_school_terms(year: int) -> List[Dict[str, Any]]:
    """Get Zimbabwe school terms for a given year"""
    terms = [
        {
            'term': 1,
            'name': 'Term 1',
            'start_date': f'{year}-01-10',
            'end_date': f'{year}-04-15',
            'description': 'First term of the academic year'
        },
        {
            'term': 2,
            'name': 'Term 2',
            'start_date': f'{year}-05-10',
            'end_date': f'{year}-08-15',
            'description': 'Second term of the academic year'
        },
        {
            'term': 3,
            'name': 'Term 3',
            'start_date': f'{year}-09-10',
            'end_date': f'{year}-12-15',
            'description': 'Third term of the academic year'
        }
    ]
    
    return terms


def calculate_academic_days(start_date: date, end_date: date, holidays: List[date] = None) -> int:
    """Calculate number of academic days between two dates"""
    if holidays is None:
        holidays = []
    
    total_days = (end_date - start_date).days + 1
    weekend_days = 0
    current_date = start_date
    
    while current_date <= end_date:
        if current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            weekend_days += 1
        current_date += timedelta(days=1)
    
    holiday_days = sum(1 for holiday in holidays if start_date <= holiday <= end_date)
    
    return total_days - weekend_days - holiday_days


# =====================================================
# VALIDATION UTILITIES
# =====================================================

def validate_zimbabwe_phone_number(phone: str) -> bool:
    """Validate Zimbabwe phone number format"""
    import re
    
    # Remove spaces and special characters
    phone = re.sub(r'[^\d+]', '', phone)
    
    # Check various formats
    patterns = [
        r'^\+263[0-9]{9}$',  # +263701234567
        r'^263[0-9]{9}$',    # 263701234567
        r'^0[0-9]{9}$',      # 0701234567
        r'^[0-9]{9}$'        # 701234567
    ]
    
    return any(re.match(pattern, phone) for pattern in patterns)


def validate_zimbabwe_id_number(id_number: str) -> bool:
    """Validate Zimbabwe national ID number format"""
    import re
    
    # Remove spaces and special characters
    id_number = re.sub(r'[^\d]', '', id_number)
    
    # Zimbabwe ID format: 8 digits + 1 check digit + 1 letter + 2 digits
    pattern = r'^[0-9]{8}[0-9][A-Z][0-9]{2}$'
    
    return re.match(pattern, id_number.upper()) is not None


def validate_grade_level(grade_level: int) -> bool:
    """Validate Zimbabwe grade level"""
    return 1 <= grade_level <= 13


def validate_term_number(term_number: int) -> bool:
    """Validate Zimbabwe term number"""
    return 1 <= term_number <= 3


def validate_subject_code(code: str) -> bool:
    """Validate subject code format"""
    import re
    return bool(re.match(r'^[A-Z]{2,10}$', code))


def validate_percentage(percentage: float) -> bool:
    """Validate percentage value"""
    return 0 <= percentage <= 100


def validate_time_range(start_time: time, end_time: time) -> bool:
    """Validate time range"""
    return end_time > start_time


def validate_date_range(start_date: date, end_date: date) -> bool:
    """Validate date range"""
    return end_date >= start_date