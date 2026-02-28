"""
Management command to seed the database with demo data.
Student: Hashim Khan (W1832028)
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import SurgeryHours

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with demo users and default surgery hours'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')

        # --- Users ---
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
                'username': 'nav.emily',
                'email': 'emily@clinic.nhs.uk',
                'first_name': 'Emily',
                'last_name': 'Wilson',
                'role': 'care_navigator',
                'password': 'navigator123!',
            },
            {
                'username': 'nav.reception',
                'email': 'reception@clinic.nhs.uk',
                'first_name': 'Priya',
                'last_name': 'Patel',
                'role': 'care_navigator',
                'password': 'navigator123!',
            },
            {
                'username': 'admin.hashim',
                'email': 'admin@clinic.nhs.uk',
                'first_name': 'Hashim',
                'last_name': 'Khan',
                'role': 'superuser',
                'password': 'superuser123!',
                'phone_number': '07843928971',
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
                'postal_code': 'E17 9LS',
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
                    f'  Created {user.get_role_display()}: {user.username} ({user.get_full_name()})'
                ))
            else:
                self.stdout.write(f'  Skipped (exists): {user.username}')

        # --- Default surgery hours (Mon-Fri 08:00-18:00, Sat 09:00-12:00, Sun closed) ---
        default_hours = [
            {'day_of_week': 0, 'open_time': '08:00', 'close_time': '18:00', 'is_closed': False},
            {'day_of_week': 1, 'open_time': '08:00', 'close_time': '18:00', 'is_closed': False},
            {'day_of_week': 2, 'open_time': '08:00', 'close_time': '18:00', 'is_closed': False},
            {'day_of_week': 3, 'open_time': '08:00', 'close_time': '18:00', 'is_closed': False},
            {'day_of_week': 4, 'open_time': '08:00', 'close_time': '18:00', 'is_closed': False},
            {'day_of_week': 5, 'open_time': '09:00', 'close_time': '12:00', 'is_closed': False},
            {'day_of_week': 6, 'open_time': '00:00', 'close_time': '00:00', 'is_closed': True},
        ]

        for h in default_hours:
            _, created = SurgeryHours.objects.update_or_create(
                day_of_week=h['day_of_week'],
                defaults=h,
            )
        self.stdout.write(self.style.SUCCESS('  Surgery hours configured (Mon-Fri 08-18, Sat 09-12, Sun closed)'))

        self.stdout.write(self.style.SUCCESS('\nDemo data seeded successfully!'))
        self.stdout.write('\nTest accounts:')
        self.stdout.write('  Clinician:       dr.smith@clinic.nhs.uk / clinician123!')
        self.stdout.write('  Care Navigator:  emily@clinic.nhs.uk / navigator123!')
        self.stdout.write('  Site Admin:      admin@clinic.nhs.uk / superuser123!')
        self.stdout.write('  Patient:         john.doe@email.com / patient123!')
