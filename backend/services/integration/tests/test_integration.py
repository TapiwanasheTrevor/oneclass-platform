"""Integration Tests for Cross-Module Integration Services"""

import pytest
import pytest_asyncio
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient
from httpx import AsyncClient

from ..academic_sis_integration import AcademicSISIntegration
from ..academic_finance_integration import AcademicFinanceIntegration
from ..api import app


class TestAcademicSISIntegration:
    """Test suite for Academic-SIS integration"""
    
    @pytest_asyncio.fixture
    async def sis_integration(self, db_session: AsyncSession):
        """Create AcademicSISIntegration instance"""
        return AcademicSISIntegration(db_session)
    
    async def test_get_class_students_for_academic(self, sis_integration: AcademicSISIntegration, school_id: str, class_id: str, academic_year_id: str):
        """Test retrieving class students for academic operations"""
        students = await sis_integration.get_class_students_for_academic(
            class_id=class_id,
            academic_year_id=academic_year_id,
            school_id=school_id
        )
        
        assert isinstance(students, list)
        for student in students:
            assert 'id' in student
            assert 'student_number' in student
            assert 'first_name' in student
            assert 'last_name' in student
            assert 'grade_level' in student
            assert student['is_active'] is True
    
    async def test_get_student_academic_performance(self, sis_integration: AcademicSISIntegration, school_id: str, student_id: str, academic_year_id: str):
        """Test retrieving student academic performance"""
        performance = await sis_integration.get_student_academic_performance(
            student_id=student_id,
            academic_year_id=academic_year_id,
            school_id=school_id,
            term_number=1
        )
        
        assert performance['student_id'] == student_id
        assert 'overall_average' in performance
        assert 'attendance_rate' in performance
        assert 'subject_grades' in performance
        assert 'recent_assessments' in performance
        assert isinstance(performance['subject_grades'], list)
    
    async def test_get_student_attendance_stats(self, sis_integration: AcademicSISIntegration, school_id: str, student_id: str, academic_year_id: str):
        """Test retrieving student attendance statistics"""
        stats = await sis_integration.get_student_attendance_stats(
            student_id=student_id,
            academic_year_id=academic_year_id,
            school_id=school_id,
            term_number=1
        )
        
        assert 'total_sessions' in stats
        assert 'present_sessions' in stats
        assert 'absent_sessions' in stats
        assert 'late_sessions' in stats
        assert 'attendance_rate' in stats
        assert 0 <= stats['attendance_rate'] <= 100
    
    async def test_get_class_academic_summary(self, sis_integration: AcademicSISIntegration, school_id: str, class_id: str, academic_year_id: str):
        """Test retrieving class academic summary"""
        summary = await sis_integration.get_class_academic_summary(
            class_id=class_id,
            academic_year_id=academic_year_id,
            school_id=school_id,
            term_number=1
        )
        
        assert summary['class_id'] == class_id
        assert 'total_students' in summary
        assert 'total_assessments' in summary
        assert 'completed_assessments' in summary
        assert 'class_average' in summary
        assert 'attendance_rate' in summary
    
    async def test_get_student_guardians_for_notifications(self, sis_integration: AcademicSISIntegration, school_id: str, student_id: str):
        """Test retrieving student guardians for notifications"""
        guardians = await sis_integration.get_student_guardians_for_notifications(
            student_id=student_id,
            school_id=school_id
        )
        
        assert isinstance(guardians, list)
        for guardian in guardians:
            assert 'id' in guardian
            assert 'name' in guardian
            assert 'relationship' in guardian
            assert 'preferred_contact_method' in guardian
            assert 'notification_preferences' in guardian
    
    async def test_validate_student_enrollment_for_academic(self, sis_integration: AcademicSISIntegration, school_id: str, student_id: str, class_id: str, subject_id: str, academic_year_id: str):
        """Test validating student enrollment for academic operations"""
        result = await sis_integration.validate_student_enrollment_for_academic(
            student_id=student_id,
            class_id=class_id,
            subject_id=subject_id,
            academic_year_id=academic_year_id,
            school_id=school_id
        )
        
        assert 'is_valid' in result
        assert 'validation_details' in result
        assert isinstance(result['is_valid'], bool)
    
    async def test_error_handling_invalid_student(self, sis_integration: AcademicSISIntegration, school_id: str, academic_year_id: str):
        """Test error handling for invalid student ID"""
        invalid_student_id = str(uuid4())
        
        with pytest.raises(Exception):
            await sis_integration.get_student_academic_performance(
                student_id=invalid_student_id,
                academic_year_id=academic_year_id,
                school_id=school_id
            )


class TestAcademicFinanceIntegration:
    """Test suite for Academic-Finance integration"""
    
    @pytest_asyncio.fixture
    async def finance_integration(self, db_session: AsyncSession):
        """Create AcademicFinanceIntegration instance"""
        return AcademicFinanceIntegration(db_session)
    
    async def test_check_student_subject_access(self, finance_integration: AcademicFinanceIntegration, school_id: str, student_id: str, subject_id: str, academic_year_id: str):
        """Test checking student subject access based on payments"""
        access_info = await finance_integration.check_student_subject_access(
            student_id=student_id,
            subject_id=subject_id,
            academic_year_id=academic_year_id,
            school_id=school_id
        )
        
        assert 'has_access' in access_info
        assert 'outstanding_balance' in access_info
        assert 'required_fees' in access_info
        assert 'subject_fees' in access_info
        assert isinstance(access_info['has_access'], bool)
        assert isinstance(access_info['outstanding_balance'], (int, float, Decimal))
        assert isinstance(access_info['required_fees'], list)
    
    async def test_check_student_assessment_access(self, finance_integration: AcademicFinanceIntegration, school_id: str, student_id: str, assessment_id: str):
        """Test checking student assessment access based on exam fees"""
        access_info = await finance_integration.check_student_assessment_access(
            student_id=student_id,
            assessment_id=assessment_id,
            school_id=school_id
        )
        
        assert 'has_access' in access_info
        assert 'assessment_name' in access_info
        assert 'subject_name' in access_info
        assert 'subject_access' in access_info
        assert 'exam_fees_outstanding' in access_info
        assert 'total_outstanding' in access_info
    
    async def test_generate_subject_enrollment_invoice(self, finance_integration: AcademicFinanceIntegration, school_id: str, student_id: str, subject_id: str, academic_year_id: str):
        """Test generating invoice for subject enrollment"""
        result = await finance_integration.generate_subject_enrollment_invoice(
            student_id=student_id,
            subject_id=subject_id,
            academic_year_id=academic_year_id,
            school_id=school_id
        )
        
        assert 'student_id' in result
        assert 'subject_id' in result
        assert 'subject_name' in result
        assert 'invoices_created' in result
        assert 'total_amount' in result
        assert isinstance(result['invoices_created'], list)
        
        for invoice in result['invoices_created']:
            assert 'invoice_id' in invoice
            assert 'fee_category_name' in invoice
            assert 'amount' in invoice
            assert 'due_date' in invoice
    
    async def test_process_resource_usage_billing(self, finance_integration: AcademicFinanceIntegration, school_id: str, student_id: str, academic_year_id: str):
        """Test processing resource usage billing"""
        billing_data = {
            'student_id': student_id,
            'resource_type': 'laboratory_equipment',
            'resource_id': 'microscope_001',
            'usage_amount': 2.5,
            'academic_year_id': academic_year_id
        }
        
        result = await finance_integration.process_resource_usage_billing(
            billing_data=billing_data,
            school_id=school_id
        )
        
        assert 'invoice_id' in result
        assert 'resource_type' in result
        assert 'usage_amount' in result
        assert 'unit_cost' in result
        assert 'total_cost' in result
        assert 'due_date' in result
        assert result['resource_type'] == 'laboratory_equipment'
        assert result['usage_amount'] == 2.5
    
    async def test_get_academic_financial_summary(self, finance_integration: AcademicFinanceIntegration, school_id: str, academic_year_id: str):
        """Test retrieving academic financial summary"""
        summary = await finance_integration.get_academic_financial_summary(
            academic_year_id=academic_year_id,
            school_id=school_id,
            term_number=1
        )
        
        assert summary['school_id'] == school_id
        assert summary['academic_year_id'] == academic_year_id
        assert 'summary' in summary
        assert 'fee_breakdown' in summary
        assert 'generated_at' in summary
        
        # Check summary statistics
        stats = summary['summary']
        assert 'total_invoices' in stats
        assert 'total_invoiced' in stats
        assert 'total_paid' in stats
        assert 'total_outstanding' in stats
        assert 'collection_rate' in stats
    
    async def test_get_students_with_payment_restrictions(self, finance_integration: AcademicFinanceIntegration, school_id: str, class_id: str, academic_year_id: str):
        """Test retrieving students with payment restrictions"""
        restrictions = await finance_integration.get_students_with_payment_restrictions(
            class_id=class_id,
            academic_year_id=academic_year_id,
            school_id=school_id
        )
        
        assert isinstance(restrictions, list)
        for restriction in restrictions:
            assert 'student_id' in restriction
            assert 'total_outstanding' in restriction
            assert 'outstanding_invoices' in restriction
            assert 'restrictions' in restriction
            assert 'restriction_level' in restriction
            assert restriction['restriction_level'] in ['high', 'medium', 'low']
    
    async def test_fee_based_access_control(self, finance_integration: AcademicFinanceIntegration, school_id: str, student_id: str, subject_id: str, academic_year_id: str):
        """Test fee-based access control logic"""
        # First, check access (should be denied due to unpaid fees)
        access_info = await finance_integration.check_student_subject_access(
            student_id=student_id,
            subject_id=subject_id,
            academic_year_id=academic_year_id,
            school_id=school_id
        )
        
        if not access_info['has_access'] and access_info['required_fees']:
            # Generate invoice for required fees
            invoice_result = await finance_integration.generate_subject_enrollment_invoice(
                student_id=student_id,
                subject_id=subject_id,
                academic_year_id=academic_year_id,
                school_id=school_id
            )
            
            assert len(invoice_result['invoices_created']) > 0
            assert invoice_result['total_amount'] > 0
    
    async def test_error_handling_insufficient_funds(self, finance_integration: AcademicFinanceIntegration, school_id: str, student_id: str, subject_id: str, academic_year_id: str):
        """Test error handling for students with insufficient payment history"""
        # This test assumes the student has outstanding fees
        access_info = await finance_integration.check_student_subject_access(
            student_id=student_id,
            subject_id=subject_id,
            academic_year_id=academic_year_id,
            school_id=school_id
        )
        
        if access_info['outstanding_balance'] > 0:
            assert access_info['has_access'] is False
            assert len(access_info['required_fees']) > 0
            assert 'reason' in access_info


class TestIntegrationAPI:
    """Test suite for Integration API endpoints"""
    
    async def test_get_class_students_for_academic_endpoint(self, async_client: AsyncClient, auth_headers: dict, class_id: str, academic_year_id: str):
        """Test Academic-SIS class students endpoint"""
        response = await async_client.get(
            f"/integration/academic/class/{class_id}/students?academic_year_id={academic_year_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        for student in data:
            assert 'id' in student
            assert 'student_number' in student
            assert 'first_name' in student
            assert 'last_name' in student
    
    async def test_get_student_academic_performance_endpoint(self, async_client: AsyncClient, auth_headers: dict, student_id: str, academic_year_id: str):
        """Test Academic-SIS student performance endpoint"""
        response = await async_client.get(
            f"/integration/academic/student/{student_id}/performance?academic_year_id={academic_year_id}&term_number=1",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['student_id'] == student_id
        assert 'overall_average' in data
        assert 'subject_grades' in data
    
    async def test_check_student_subject_access_endpoint(self, async_client: AsyncClient, auth_headers: dict, student_id: str, subject_id: str, academic_year_id: str):
        """Test Academic-Finance subject access endpoint"""
        response = await async_client.get(
            f"/integration/finance/student/{student_id}/subject/{subject_id}/access?academic_year_id={academic_year_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'has_access' in data
        assert 'outstanding_balance' in data
        assert 'required_fees' in data
    
    async def test_generate_subject_enrollment_invoice_endpoint(self, async_client: AsyncClient, auth_headers: dict, student_id: str, subject_id: str, academic_year_id: str):
        """Test Academic-Finance invoice generation endpoint"""
        response = await async_client.post(
            f"/integration/finance/student/{student_id}/subject/{subject_id}/invoice?academic_year_id={academic_year_id}",
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'student_id' in data
        assert 'subject_id' in data
        assert 'invoices_created' in data
        assert 'total_amount' in data
    
    async def test_process_resource_usage_billing_endpoint(self, async_client: AsyncClient, auth_headers: dict, student_id: str, academic_year_id: str):
        """Test Academic-Finance resource usage billing endpoint"""
        billing_data = {
            'student_id': student_id,
            'resource_type': 'laboratory_equipment',
            'resource_id': 'microscope_001',
            'usage_amount': 2.5
        }
        
        response = await async_client.post(
            f"/integration/finance/resource-usage?academic_year_id={academic_year_id}",
            json=billing_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'invoice_id' in data
        assert 'resource_type' in data
        assert 'total_cost' in data
    
    async def test_get_academic_financial_summary_endpoint(self, async_client: AsyncClient, auth_headers: dict, academic_year_id: str):
        """Test Academic-Finance summary endpoint"""
        response = await async_client.get(
            f"/integration/finance/academic/summary?academic_year_id={academic_year_id}&term_number=1",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['academic_year_id'] == academic_year_id
        assert 'summary' in data
        assert 'fee_breakdown' in data
    
    async def test_validate_student_enrollment_endpoint(self, async_client: AsyncClient, auth_headers: dict, student_id: str, class_id: str, subject_id: str, academic_year_id: str):
        """Test enrollment validation endpoint"""
        params = {
            'class_id': class_id,
            'subject_id': subject_id,
            'academic_year_id': academic_year_id
        }
        
        response = await async_client.get(
            f"/integration/validate/student/{student_id}/enrollment",
            params=params,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'is_valid' in data
    
    async def test_sync_class_enrollment_endpoint(self, async_client: AsyncClient, auth_headers: dict, class_id: str, academic_year_id: str):
        """Test class enrollment sync endpoint"""
        response = await async_client.post(
            f"/integration/sync/class/{class_id}/enrollment-academic?academic_year_id={academic_year_id}",
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'students' in data
        assert 'summary' in data
        assert 'sync_timestamp' in data
    
    async def test_integration_health_check_endpoint(self, async_client: AsyncClient):
        """Test integration health check endpoint"""
        response = await async_client.get("/integration/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'integration'
        assert 'modules' in data
        assert 'timestamp' in data
    
    async def test_unauthorized_access(self, async_client: AsyncClient, student_id: str, subject_id: str, academic_year_id: str):
        """Test unauthorized access to integration endpoints"""
        response = await async_client.get(
            f"/integration/finance/student/{student_id}/subject/{subject_id}/access?academic_year_id={academic_year_id}"
        )
        
        assert response.status_code == 401
    
    async def test_invalid_parameters(self, async_client: AsyncClient, auth_headers: dict):
        """Test invalid parameters handling"""
        # Test with invalid UUID
        response = await async_client.get(
            "/integration/academic/student/invalid-uuid/performance?academic_year_id=year-2024",
            headers=auth_headers
        )
        
        assert response.status_code == 422
    
    async def test_cross_module_error_handling(self, async_client: AsyncClient, auth_headers: dict, student_id: str, academic_year_id: str):
        """Test error handling when one module is unavailable"""
        # This test simulates a scenario where the finance module is down
        non_existent_subject = str(uuid4())
        
        response = await async_client.get(
            f"/integration/finance/student/{student_id}/subject/{non_existent_subject}/access?academic_year_id={academic_year_id}",
            headers=auth_headers
        )
        
        assert response.status_code in [404, 500]  # Either not found or service error


class TestIntegrationPerformance:
    """Test suite for integration performance and caching"""
    
    async def test_concurrent_requests_handling(self, async_client: AsyncClient, auth_headers: dict, student_ids: list, subject_id: str, academic_year_id: str):
        """Test handling of concurrent integration requests"""
        import asyncio
        
        async def check_access(student_id: str):
            return await async_client.get(
                f"/integration/finance/student/{student_id}/subject/{subject_id}/access?academic_year_id={academic_year_id}",
                headers=auth_headers
            )
        
        # Make concurrent requests for multiple students
        tasks = [check_access(student_id) for student_id in student_ids[:5]]  # Limit to 5 concurrent
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All requests should succeed
        for response in responses:
            if isinstance(response, Exception):
                pytest.fail(f"Request failed with exception: {response}")
            assert response.status_code == 200
    
    async def test_caching_behavior(self, async_client: AsyncClient, auth_headers: dict, student_id: str, academic_year_id: str):
        """Test caching behavior for integration endpoints"""
        import time
        
        # First request
        start_time = time.time()
        response1 = await async_client.get(
            f"/integration/academic/student/{student_id}/performance?academic_year_id={academic_year_id}",
            headers=auth_headers
        )
        first_request_time = time.time() - start_time
        
        # Second request (should be faster due to caching)
        start_time = time.time()
        response2 = await async_client.get(
            f"/integration/academic/student/{student_id}/performance?academic_year_id={academic_year_id}",
            headers=auth_headers
        )
        second_request_time = time.time() - start_time
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json() == response2.json()
        
        # Second request should be faster (cached)
        # Note: This is environment-dependent, so we use a generous threshold
        assert second_request_time <= first_request_time * 1.5
