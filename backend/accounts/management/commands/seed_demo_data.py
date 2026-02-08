"""
Management command to seed the database with demo data for the IPD demonstration.
Student: Hashim Khan (W1832028)
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with demo users for the AI Triage System'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')

        # Create demo users
        users = [
            {
                'username': 'dr.smith',
                'email': 'dr.smith@clinic.nhs.uk',
                'first_name': 'Sarah',
                'last_name': 'Smith',
                'role': 'clinician',
                'password': 'clinician123!',
            },
            {
                'username': 'dr.jones',
                'email': 'dr.jones@clinic.nhs.uk',
                'first_name': 'James',
                'last_name': 'Jones',
                'role': 'clinician',
                'password': 'clinician123!',
            },
            {
                'username': 'admin.staff',
                'email': 'admin@clinic.nhs.uk',
                'first_name': 'Hashim',
                'last_name': 'Khan',
                'role': 'admin',
                'password': 'admin123!',
                'phone_number': '07843928971',
            },
            {
                'username': 'receptionist',
                'email': 'reception@clinic.nhs.uk',
                'first_name': 'Emily',
                'last_name': 'Wilson',
                'role': 'admin',
                'password': 'admin123!',
            },
            {
                'username': 'john.patient',
                'email': 'john.doe@email.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'patient',
                'password': 'patient123!',
                'phone_number': '07700900001',
                'nhs_number': '9876543210',
                'postal_code': 'W14 8QS',
            },
            {
                'username': 'jane.patient',
                'email': 'jane.smith@email.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'role': 'patient',
                'password': 'patient123!',
                'phone_number': '07700900002',
                'nhs_number': '1234567890',
                'postal_code': 'W6 7HL',
            },
            {
                'username': 'adil.khan',
                'email': 'adilkhan1969@hotmail.com',
                'first_name': 'Adil',
                'last_name': 'Khan',
                'role': 'patient',
                'password': 'patient123!',
                'phone_number': '07487861821',
                'nhs_number': '6503492235',
                'postal_code': 'E17 9ls',
            },
        ]

        for user_data in users:
            password = user_data.pop('password')
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data,
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f'  Created {user.role}: {user.username} ({user.get_full_name()})'
                ))
            else:
                self.stdout.write(f'  Skipped (exists): {user.username}')

        self.stdout.write(self.style.SUCCESS('\nDemo data seeded successfully!'))
        self.stdout.write('\nTest accounts:')
        self.stdout.write('  Clinician: dr.smith / clinician123!')
        self.stdout.write('  Admin: admin.staff / admin123!')
        self.stdout.write('  Patient: john.patient / patient123!')
