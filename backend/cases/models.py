from django.db import models
from django.conf import settings
import uuid


class PatientCase(models.Model):
    """A patient's triage case submitted through the system."""

    class Urgency(models.TextChoices):
        EMERGENCY = 'emergency', 'Emergency (999/A&E)'
        URGENT = 'urgent', 'Urgent (1-2 days)'
        ROUTINE = 'routine', 'Routine (2-3 weeks)'
        SELF_CARE = 'self_care', 'Self-care / Non-urgent'

    class Status(models.TextChoices):
        NEW = 'new', 'New Patient Case'
        IN_PROGRESS = 'in_progress', 'In Progress (Clinician Reviewing)'
        DECIDED = 'decided', 'Decided (Awaiting Admin Action)'
        CLOSED = 'closed', 'Closed'

    class ClosureReason(models.TextChoices):
        APPOINTMENT_BOOKED = 'appointment_booked', 'Appointment Booked'
        URGENT_REFERRAL = 'urgent_referral', 'Urgent Referral (A&E/999)'
        FOLLOW_UP = 'follow_up', 'Follow-up Appointment'
        SELF_CARE_ADVISED = 'self_care_advised', 'Self-care Advised'
        REFERRED_111 = 'referred_111', '111 Referral'
        EXTENDED_ACCESS = 'extended_access', 'Extended Access'
        NO_CONTACT_REQUIRED = 'no_contact_required', 'No Contact Required'
        MESSAGE_SENT = 'message_sent', 'Message Sent to Patient'
        OTHER = 'other', 'Other'

    # Identifiers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case_number = models.CharField(max_length=20, unique=True, editable=False)

    # Patient info
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cases',
    )

    # Symptom submission (mimicking Klinik form)
    visit_type = models.CharField(max_length=100, default='New medical issue')
    body_location = models.CharField(max_length=100, blank=True)
    symptom_duration = models.CharField(max_length=100, blank=True)
    symptoms_text = models.TextField(help_text="Patient's description of symptoms")
    selected_symptoms = models.JSONField(
        default=list, blank=True,
        help_text="Structured symptom selections"
    )
    severity_symptoms = models.JSONField(
        default=list, blank=True,
        help_text="Severity/red-flag symptoms selected"
    )
    additional_info = models.TextField(blank=True)
    previous_treatment = models.BooleanField(default=False)
    previously_seen = models.BooleanField(default=False)

    # AI Triage suggestion
    ai_urgency = models.CharField(
        max_length=20, choices=Urgency.choices, blank=True,
        help_text="AI-suggested urgency level"
    )
    ai_confidence = models.FloatField(
        null=True, blank=True,
        help_text="AI confidence score (0-1)"
    )
    ai_rationale = models.TextField(
        blank=True,
        help_text="AI explanation for the suggested urgency"
    )
    ai_differential = models.JSONField(
        default=list, blank=True,
        help_text="AI differential diagnosis suggestions"
    )

    # Clinician decision
    clinician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='triaged_cases',
    )
    clinician_urgency = models.CharField(
        max_length=20, choices=Urgency.choices, blank=True,
        help_text="Clinician's final urgency decision"
    )
    clinician_notes = models.TextField(blank=True)
    clinician_decision_at = models.DateTimeField(null=True, blank=True)

    # Admin/closure
    admin_handler = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='handled_cases',
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NEW,
    )
    closure_reason = models.CharField(
        max_length=30, choices=ClosureReason.choices, blank=True,
    )
    closure_notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Case {self.case_number} - {self.patient.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.case_number:
            import random
            import string
            self.case_number = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        super().save(*args, **kwargs)


class AuditLog(models.Model):
    """Complete audit trail for all actions on a case. Required for clinical safety."""

    class Action(models.TextChoices):
        CREATED = 'created', 'Case Created'
        AI_TRIAGED = 'ai_triaged', 'AI Triage Completed'
        CLINICIAN_REVIEWED = 'clinician_reviewed', 'Clinician Reviewed'
        CLINICIAN_DECIDED = 'clinician_decided', 'Clinician Decision Made'
        REDIRECTED = 'redirected', 'Redirected to Another Unit'
        ADMIN_ACTIONED = 'admin_actioned', 'Admin Action Taken'
        CLOSED = 'closed', 'Case Closed'
        REOPENED = 'reopened', 'Case Reopened'
        NOTE_ADDED = 'note_added', 'Note Added'

    case = models.ForeignKey(PatientCase, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    action = models.CharField(max_length=30, choices=Action.choices)
    details = models.TextField(blank=True)
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} on {self.case.case_number} at {self.timestamp}"
