# cases/views.py - all the API endpoints for triage cases
# handles patient submissions, clinician decisions, navigator closures
# and the dashboard stats

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q
from django.db import models as db_models

from .models import PatientCase, AuditLog
from .serializers import (
    PatientCaseCreateSerializer,
    PatientCaseListSerializer,
    PatientCaseDetailSerializer,
    ClinicianDecisionSerializer,
    AdminCloseSerializer,
)


# --- permission classes ---
# each one checks if the user has the right role to access the endpoint

class IsPatient(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'patient'


class IsClinician(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'clinician'


class IsCareNavigator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'care_navigator'


class IsSuperuser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'superuser'


class IsStaff(permissions.BasePermission):
    """any non-patient user (clinician, navigator, or superuser)"""
    def has_permission(self, request, view):
        return request.user.role in ('clinician', 'care_navigator', 'superuser')


# --- patient endpoints ---

class PatientSubmitCase(generics.CreateAPIView):
    """patient submits a new case - the AI triage runs automatically in the serializer"""
    serializer_class = PatientCaseCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def create(self, request, *args, **kwargs):
        # check if the surgery is actually open before letting them submit
        from accounts.models import SurgeryHours
        now = timezone.localtime()
        current_day = now.weekday()
        current_time = now.time()

        try:
            hours = SurgeryHours.objects.get(day_of_week=current_day)
            if hours.is_closed:
                return Response(
                    {"detail": "The surgery is closed today. Please try again on the next working day."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if not (hours.open_time <= current_time <= hours.close_time):
                return Response(
                    {"detail": f"The surgery is currently closed. Opening hours today are {hours.open_time:%H:%M} - {hours.close_time:%H:%M}."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except SurgeryHours.DoesNotExist:
            pass  # no hours set up = always open (default)

        return super().create(request, *args, **kwargs)


class PatientMyCases(generics.ListAPIView):
    """patient can only see their own cases"""
    serializer_class = PatientCaseListSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def get_queryset(self):
        return PatientCase.objects.filter(patient=self.request.user)


# --- staff endpoints ---

class ClinicianCaseList(generics.ListAPIView):
    """staff can see all cases, with optional status/urgency filters"""
    serializer_class = PatientCaseListSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaff]

    def get_queryset(self):
        qs = PatientCase.objects.all()
        # let them filter by status or urgency from the query string
        status_filter = self.request.query_params.get('status')
        urgency_filter = self.request.query_params.get('urgency')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if urgency_filter:
            qs = qs.filter(ai_urgency=urgency_filter)
        return qs


class CaseDetail(generics.RetrieveAPIView):
    """full case detail - patients can only see their own, staff can see all"""
    serializer_class = PatientCaseDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return PatientCase.objects.filter(patient=user)
        return PatientCase.objects.all()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsClinician])
def clinician_decide(request, case_id):
    """clinician makes their triage decision on a case"""
    try:
        case = PatientCase.objects.get(id=case_id)
    except PatientCase.DoesNotExist:
        return Response({"detail": "Case not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = ClinicianDecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    old_status = case.status
    case.clinician = request.user
    case.clinician_urgency = serializer.validated_data['clinician_urgency']
    case.clinician_notes = serializer.validated_data.get('clinician_notes', '')
    case.clinician_decision_at = timezone.now()
    case.status = PatientCase.Status.DECIDED
    case.save()

    # log it in the audit trail
    AuditLog.objects.create(
        case=case, user=request.user,
        action=AuditLog.Action.CLINICIAN_DECIDED,
        details=f"Decision: {case.get_clinician_urgency_display()}. Notes: {case.clinician_notes}",
        previous_status=old_status,
        new_status='decided',
    )

    return Response(PatientCaseDetailSerializer(case).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def navigator_close_case(request, case_id):
    """care navigator or superuser closes a case after clinician has decided"""
    if request.user.role not in ('care_navigator', 'superuser'):
        return Response({"detail": "Not authorised."}, status=status.HTTP_403_FORBIDDEN)

    try:
        case = PatientCase.objects.get(id=case_id)
    except PatientCase.DoesNotExist:
        return Response({"detail": "Case not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = AdminCloseSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    old_status = case.status
    case.admin_handler = request.user
    case.closure_reason = serializer.validated_data['closure_reason']
    case.closure_notes = serializer.validated_data.get('closure_notes', '')
    case.status = PatientCase.Status.CLOSED
    case.closed_at = timezone.now()
    case.save()

    # log it
    AuditLog.objects.create(
        case=case, user=request.user,
        action=AuditLog.Action.CLOSED,
        details=f"Closed: {case.get_closure_reason_display()}. {case.closure_notes}",
        previous_status=old_status,
        new_status='closed',
    )

    return Response(PatientCaseDetailSerializer(case).data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsStaff])
def dashboard_stats(request):
    """returns aggregate stats for the staff dashboard"""
    cases = PatientCase.objects.all()
    today = timezone.now().date()

    stats = {
        'total_cases': cases.count(),
        'new_cases': cases.filter(status='new').count(),
        'in_progress': cases.filter(status='in_progress').count(),
        'decided': cases.filter(status='decided').count(),
        'closed': cases.filter(status='closed').count(),
        'today_cases': cases.filter(created_at__date=today).count(),
        'urgency_breakdown': {
            'emergency': cases.filter(ai_urgency='emergency').count(),
            'urgent': cases.filter(ai_urgency='urgent').count(),
            'routine': cases.filter(ai_urgency='routine').count(),
            'self_care': cases.filter(ai_urgency='self_care').count(),
        },
        'ai_agreement_rate': _calculate_agreement_rate(cases),
    }
    return Response(stats)


def _calculate_agreement_rate(cases):
    """works out how often clinicians agree with the AI's suggestion"""
    from django.db.models import F
    decided = cases.filter(
        clinician_urgency__isnull=False,
        ai_urgency__isnull=False,
    ).exclude(clinician_urgency='').exclude(ai_urgency='')

    if not decided.exists():
        return None

    agreed = decided.filter(clinician_urgency=F('ai_urgency')).count()
    return round(agreed / decided.count() * 100, 1)
