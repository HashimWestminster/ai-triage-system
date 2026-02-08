from django.contrib import admin
from .models import PatientCase, AuditLog


@admin.register(PatientCase)
class PatientCaseAdmin(admin.ModelAdmin):
    list_display = ['case_number', 'patient', 'visit_type', 'status', 'ai_urgency', 'clinician_urgency', 'created_at']
    list_filter = ['status', 'ai_urgency', 'clinician_urgency']
    search_fields = ['case_number', 'patient__first_name', 'patient__last_name']
    readonly_fields = ['id', 'case_number', 'created_at', 'updated_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['case', 'user', 'action', 'timestamp']
    list_filter = ['action']
    readonly_fields = ['timestamp']
