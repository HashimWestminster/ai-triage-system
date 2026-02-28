from rest_framework import serializers
from .models import PatientCase, AuditLog
from accounts.serializers import UserSerializer


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = '__all__'

    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name()
        return 'System'


class PatientCaseCreateSerializer(serializers.ModelSerializer):
    """Serializer for patients submitting a new case."""

    class Meta:
        model = PatientCase
        fields = [
            'visit_type', 'body_location', 'symptom_duration',
            'symptoms_text', 'selected_symptoms', 'severity_symptoms',
            'additional_info', 'previous_treatment', 'previously_seen',
        ]

    def create(self, validated_data):
        validated_data['patient'] = self.context['request'].user
        case = PatientCase.objects.create(**validated_data)

        # Run AI triage
        from ai_engine.triage import TriageEngine
        engine = TriageEngine()
        result = engine.assess(
            symptoms_text=validated_data.get('symptoms_text', ''),
            selected_symptoms=validated_data.get('selected_symptoms', []),
            severity_symptoms=validated_data.get('severity_symptoms', []),
            body_location=validated_data.get('body_location', ''),
            duration=validated_data.get('symptom_duration', ''),
        )

        case.ai_urgency = result['urgency']
        case.ai_confidence = result['confidence']
        case.ai_rationale = result['rationale']
        case.ai_differential = result.get('differential', [])
        case.save()

        # Audit log
        AuditLog.objects.create(
            case=case, user=case.patient,
            action=AuditLog.Action.CREATED,
            details=f"Case submitted: {validated_data.get('visit_type', 'New issue')}",
            new_status='new',
        )
        AuditLog.objects.create(
            case=case, user=None,
            action=AuditLog.Action.AI_TRIAGED,
            details=f"AI suggested: {result['urgency']} (confidence: {result['confidence']:.0%}). {result['rationale']}",
        )

        return case


class PatientCaseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for case lists."""
    patient_name = serializers.SerializerMethodField()
    clinician_name = serializers.SerializerMethodField()

    class Meta:
        model = PatientCase
        fields = [
            'id', 'case_number', 'patient_name', 'visit_type',
            'body_location', 'status', 'ai_urgency', 'clinician_urgency',
            'clinician_name', 'created_at', 'updated_at',
        ]

    def get_patient_name(self, obj):
        return obj.patient.get_full_name()

    def get_clinician_name(self, obj):
        if obj.clinician:
            return obj.clinician.get_full_name()
        return None


class PatientCaseDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer for viewing a case."""
    patient = UserSerializer(read_only=True)
    clinician = UserSerializer(read_only=True)
    admin_handler = UserSerializer(read_only=True)
    audit_logs = AuditLogSerializer(many=True, read_only=True)

    class Meta:
        model = PatientCase
        fields = '__all__'


class ClinicianDecisionSerializer(serializers.Serializer):
    """Serializer for clinician making a triage decision."""
    clinician_urgency = serializers.ChoiceField(choices=PatientCase.Urgency.choices)
    clinician_notes = serializers.CharField(required=False, allow_blank=True)


class AdminCloseSerializer(serializers.Serializer):
    """Serializer for admin closing a case."""
    closure_reason = serializers.ChoiceField(choices=PatientCase.ClosureReason.choices)
    closure_notes = serializers.CharField(required=False, allow_blank=True)
