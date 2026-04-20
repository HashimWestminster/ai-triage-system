"""
Group 3: Access Control, Clinician Workflow, and Audit Trail Tests
Tests role-based access, clinician decisions, and audit logging.

Run: cd backend && python manage.py test cases.tests -v 2
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from cases.models import PatientCase, AuditLog

User = get_user_model()


class Group3_AccessControl(TestCase):
    """Tests for role-based access control (FR6)."""

    def setUp(self):
        self.client = APIClient()
        self.patient = User.objects.create_user(
            username='testpatient',
            email='patient@test.com',
            password='testpass123!',
            role='patient',
            first_name='John',
            last_name='Patient',
        )
        self.clinician = User.objects.create_user(
            username='testclinician',
            email='clinician@test.com',
            password='testpass123!',
            role='clinician',
            first_name='Sarah',
            last_name='Smith',
        )
        self.admin = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123!',
            role='administrator',
            first_name='Admin',
            last_name='Staff',
        )

    def test_01_patient_cannot_see_case_list(self):
        """Patient should NOT be able to access the clinician case list."""
        self.client.force_authenticate(user=self.patient)
        response = self.client.get('/api/cases/list/')
        print(f"\n  Patient accessing case list: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_02_clinician_can_see_case_list(self):
        """Clinician SHOULD be able to access the case list."""
        self.client.force_authenticate(user=self.clinician)
        response = self.client.get('/api/cases/list/')
        print(f"\n  Clinician accessing case list: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_03_admin_can_see_case_list(self):
        """Admin SHOULD be able to access the case list."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/cases/list/')
        print(f"\n  Admin accessing case list: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_04_unauthenticated_blocked_everywhere(self):
        """No token at all should be blocked on every endpoint."""
        endpoints = [
            '/api/cases/submit/',
            '/api/cases/list/',
            '/api/cases/my-cases/',
            '/api/cases/dashboard/stats/',
        ]
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            print(f"\n  Unauthenticated -> {endpoint}: {response.status_code}")
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_05_clinician_cannot_submit_case(self):
        """Clinician should NOT be able to submit a patient case."""
        self.client.force_authenticate(user=self.clinician)
        data = {
            'visit_type': 'New medical issue',
            'symptoms_text': 'Test submission from clinician',
        }
        response = self.client.post('/api/cases/submit/', data, format='json')
        print(f"\n  Clinician submitting case: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_06_patient_cannot_make_decision(self):
        """Patient should NOT be able to make a clinician decision."""
        self.client.force_authenticate(user=self.patient)
        response = self.client.post(
            '/api/cases/00000000-0000-0000-0000-000000000000/decide/',
            {'clinician_urgency': 'routine', 'clinician_notes': 'test'},
            format='json'
        )
        print(f"\n  Patient making decision: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class Group3_ClinicianWorkflow(TestCase):
    """Tests for the clinician decision workflow (FR4)."""

    def setUp(self):
        self.client = APIClient()
        self.patient = User.objects.create_user(
            username='testpatient2',
            email='patient2@test.com',
            password='testpass123!',
            role='patient',
            first_name='Test',
            last_name='Patient',
        )
        self.clinician = User.objects.create_user(
            username='testclinician2',
            email='clinician2@test.com',
            password='testpass123!',
            role='clinician',
            first_name='Dr',
            last_name='Test',
        )

    def _create_case(self):
        self.client.force_authenticate(user=self.patient)
        data = {
            'visit_type': 'New medical issue',
            'body_location': 'Back',
            'symptom_duration': '2-4 weeks',
            'symptoms_text': 'Lower back pain for three weeks',
            'selected_symptoms': ['Back pain'],
            'severity_symptoms': [],
            'additional_info': '',
            'previous_treatment': False,
            'previously_seen': False,
        }
        response = self.client.post('/api/cases/submit/', data, format='json')
        return response.data.get('id')

    def test_07_clinician_agrees_with_ai(self):
        """Clinician confirms the AI suggestion."""
        case_id = self._create_case()
        self.assertIsNotNone(case_id)
        case = PatientCase.objects.get(id=case_id)
        ai_urgency = case.ai_urgency

        self.client.force_authenticate(user=self.clinician)
        decision = {
            'clinician_urgency': ai_urgency,
            'clinician_notes': 'Agree with AI assessment.',
        }
        response = self.client.post(
            f'/api/cases/{case_id}/decide/', decision, format='json'
        )
        print(f"\n  Clinician agrees with AI ({ai_urgency}): {response.status_code}")
        self.assertIn(response.status_code, [200, 201])

        case.refresh_from_db()
        print(f"  Case status after decision: {case.status}")
        self.assertEqual(case.status, 'decided')

    def test_08_clinician_overrides_ai(self):
        """Clinician picks a different urgency than the AI suggested."""
        case_id = self._create_case()
        self.assertIsNotNone(case_id)

        self.client.force_authenticate(user=self.clinician)
        decision = {
            'clinician_urgency': 'urgent',
            'clinician_notes': 'Patient history warrants urgent review.',
        }
        response = self.client.post(
            f'/api/cases/{case_id}/decide/', decision, format='json'
        )
        print(f"\n  Clinician overrides to urgent: {response.status_code}")
        self.assertIn(response.status_code, [200, 201])

        case = PatientCase.objects.get(id=case_id)
        print(f"  AI said: {case.ai_urgency}, Clinician said: {case.clinician_urgency}")
        self.assertEqual(case.clinician_urgency, 'urgent')


class Group3_AuditTrail(TestCase):
    """Tests for the audit trail (FR5)."""

    def setUp(self):
        self.client = APIClient()
        self.patient = User.objects.create_user(
            username='testpatient3',
            email='patient3@test.com',
            password='testpass123!',
            role='patient',
            first_name='Audit',
            last_name='Test',
        )
        self.clinician = User.objects.create_user(
            username='testclinician3',
            email='clinician3@test.com',
            password='testpass123!',
            role='clinician',
            first_name='Dr',
            last_name='Audit',
        )

    def test_09_submission_creates_two_audit_entries(self):
        """Submitting a case should create 'created' and 'ai_triaged' entries."""
        self.client.force_authenticate(user=self.patient)
        data = {
            'visit_type': 'New medical issue',
            'body_location': 'Head',
            'symptom_duration': 'Hours',
            'symptoms_text': 'Mild headache since this morning',
            'selected_symptoms': [],
            'severity_symptoms': [],
            'additional_info': '',
            'previous_treatment': False,
            'previously_seen': False,
        }
        response = self.client.post('/api/cases/submit/', data, format='json')
        case_id = response.data.get('id')

        logs = AuditLog.objects.filter(case_id=case_id).order_by('timestamp')
        actions = [log.action for log in logs]
        print(f"\n  Audit entries after submission: {actions}")
        self.assertIn('created', actions)
        self.assertIn('ai_triaged', actions)
        self.assertGreaterEqual(logs.count(), 2)

    def test_10_decision_adds_audit_entry(self):
        """Clinician decision should add a 'clinician_decided' entry."""
        # Create case
        self.client.force_authenticate(user=self.patient)
        data = {
            'visit_type': 'New medical issue',
            'body_location': 'Back',
            'symptom_duration': '1-2 weeks',
            'symptoms_text': 'Sore back after lifting',
            'selected_symptoms': [],
            'severity_symptoms': [],
            'additional_info': '',
            'previous_treatment': False,
            'previously_seen': False,
        }
        response = self.client.post('/api/cases/submit/', data, format='json')
        case_id = response.data.get('id')

        # Clinician decides
        self.client.force_authenticate(user=self.clinician)
        decision = {
            'clinician_urgency': 'routine',
            'clinician_notes': 'Standard back strain.',
        }
        self.client.post(f'/api/cases/{case_id}/decide/', decision, format='json')

        logs = AuditLog.objects.filter(case_id=case_id).order_by('timestamp')
        actions = [log.action for log in logs]
        print(f"\n  Audit entries after decision: {actions}")
        self.assertIn('clinician_decided', actions)
        self.assertGreaterEqual(logs.count(), 3)

    def test_11_full_lifecycle_audit(self):
        """Full case lifecycle should produce at least 3 audit entries."""
        # Submit
        self.client.force_authenticate(user=self.patient)
        data = {
            'visit_type': 'New medical issue',
            'body_location': 'Legs',
            'symptom_duration': '3-7 days',
            'symptoms_text': 'Twisted my ankle while running',
            'selected_symptoms': [],
            'severity_symptoms': [],
            'additional_info': '',
            'previous_treatment': True,
            'previously_seen': False,
        }
        response = self.client.post('/api/cases/submit/', data, format='json')
        case_id = response.data.get('id')

        # Clinician decides
        self.client.force_authenticate(user=self.clinician)
        self.client.post(
            f'/api/cases/{case_id}/decide/',
            {'clinician_urgency': 'routine', 'clinician_notes': 'Minor sprain.'},
            format='json'
        )

        # Check full trail
        logs = AuditLog.objects.filter(case_id=case_id).order_by('timestamp')
        print(f"\n  Full lifecycle audit trail:")
        for log in logs:
            print(f"    {log.action} by {log.user} at {log.timestamp}")
        self.assertGreaterEqual(logs.count(), 3)