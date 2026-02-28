from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with role-based access for the triage system."""

    class Role(models.TextChoices):
        PATIENT = 'patient', 'Patient'
        CLINICIAN = 'clinician', 'Clinician'
        CARE_NAVIGATOR = 'care_navigator', 'Care Navigator'
        SUPERUSER = 'superuser', 'Site Super User'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PATIENT,
    )
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    nhs_number = models.CharField(max_length=10, blank=True, unique=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT

    @property
    def is_clinician(self):
        return self.role == self.Role.CLINICIAN

    @property
    def is_care_navigator(self):
        return self.role == self.Role.CARE_NAVIGATOR

    @property
    def is_superuser_staff(self):
        return self.role == self.Role.SUPERUSER


class SurgeryHours(models.Model):
    """Configurable opening hours - patients can only submit cases during these windows."""

    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    day_of_week = models.IntegerField(choices=DAY_CHOICES, unique=True)
    open_time = models.TimeField(default='08:00')
    close_time = models.TimeField(default='18:00')
    is_closed = models.BooleanField(default=False, help_text="If ticked, the surgery is closed all day")

    class Meta:
        ordering = ['day_of_week']
        verbose_name_plural = 'Surgery hours'

    def __str__(self):
        if self.is_closed:
            return f"{self.get_day_of_week_display()}: Closed"
        return f"{self.get_day_of_week_display()}: {self.open_time:%H:%M} - {self.close_time:%H:%M}"
