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


class IsPatient(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'patient'


class IsClinician(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'clinician'


class IsAdminStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'admin'


class IsClinicianOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ('clinician', 'admin')


# --- Patient endpoints ---

class PatientSubmitCase(generics.CreateAPIView):
    """Patient submits a new case. AI triage runs automatically."""
    serializer_class = PatientCaseCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]


class PatientMyCases(generics.ListAPIView):
    """Patient views their own cases."""
    serializer_class = PatientCaseListSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def get_queryset(self):
        return PatientCase.objects.filter(patient=self.request.user)


# --- Clinician endpoints ---

class ClinicianCaseList(generics.ListAPIView):
    """Clinician views all cases that need review."""
    serializer_class = PatientCaseListSerializer
    permission_classes = [permissions.IsAuthenticated, IsClinicianOrAdmin]

    def get_queryset(self):
        qs = PatientCase.objects.all()
        status_filter = self.request.query_params.get('status')
        urgency_filter = self.request.query_params.get('urgency')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if urgency_filter:
            qs = qs.filter(ai_urgency=urgency_filter)
        return qs


class CaseDetail(generics.RetrieveAPIView):
    """View full case detail (clinician/admin)."""
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
    """Clinician makes a triage decision on a case."""
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

    AuditLog.objects.create(
        case=case, user=request.user,
        action=AuditLog.Action.CLINICIAN_DECIDED,
        details=f"Decision: {case.get_clinician_urgency_display()}. Notes: {case.clinician_notes}",
        previous_status=old_status,
        new_status='decided',
    )

    return Response(PatientCaseDetailSerializer(case).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsAdminStaff])
def admin_close_case(request, case_id):
    """Admin closes a case with a closure reason."""
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

    AuditLog.objects.create(
        case=case, user=request.user,
        action=AuditLog.Action.CLOSED,
        details=f"Closed: {case.get_closure_reason_display()}. {case.closure_notes}",
        previous_status=old_status,
        new_status='closed',
    )

    return Response(PatientCaseDetailSerializer(case).data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsClinicianOrAdmin])
def dashboard_stats(request):
    """Dashboard statistics for clinicians/admin."""
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
    """Calculate how often clinicians agree with AI suggestion."""
    from django.db.models import F
    decided = cases.filter(
        clinician_urgency__isnull=False,
        ai_urgency__isnull=False,
    ).exclude(clinician_urgency='').exclude(ai_urgency='')

    if not decided.exists():
        return None

    agreed = decided.filter(clinician_urgency=F('ai_urgency')).count()
    return round(agreed / decided.count() * 100, 1)



