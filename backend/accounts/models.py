from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with role-based access control."""

    class Role(models.TextChoices):
        PATIENT = 'patient', 'Patient'
        CLINICIAN = 'clinician', 'Clinician'
        ADMIN = 'admin', 'Administrator'

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
    def is_admin_staff(self):
        return self.role == self.Role.ADMIN
