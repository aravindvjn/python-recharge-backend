from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import OTP
from decimal import Decimal
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create demo Recharge Backend users with realistic login credentials'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of users to create (default: 10)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing users before creating new ones',
        )

    def handle(self, *args, **options):
        count = options['count']
        
        if options['clear']:
            self.stdout.write('Clearing existing users...')
            User.objects.filter(is_superuser=False).delete()
            OTP.objects.all().delete()
        
        # Sample user data
        first_names = ['Raj', 'Priya', 'Amit', 'Neha', 'Rohit', 'Kavya', 'Suresh', 'Pooja', 'Vikash', 'Anita', 
                       'Ravi', 'Sunita', 'Deepak', 'Meera', 'Ajay', 'Sita', 'Ramesh', 'Geeta', 'Mohan', 'Radha']
        last_names = ['Sharma', 'Gupta', 'Singh', 'Verma', 'Kumar', 'Patel', 'Shah', 'Agarwal', 'Jain', 'Mehta',
                      'Yadav', 'Pandey', 'Mishra', 'Tiwari', 'Srivastava', 'Chandra', 'Prasad', 'Thakur', 'Joshi', 'Nair']
        
        # Create Recharge Backend admin user
        admin_user, created = User.objects.get_or_create(
            email='admin@rechargebackend.com',
            defaults={
                'username': 'admin@rechargebackend.com',
                'first_name': 'Recharge',
                'last_name': 'Admin',
                'phone': '9999999999',
                'user_type': 1,  # Admin
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('rechargebackend123')
            admin_user.save()
            self.stdout.write(f'Created Recharge Backend admin user: {admin_user.email}')
        
        # Create client users
        users_created = 0
        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            
            # Generate unique email and phone
            email = f'{first_name.lower()}.{last_name.lower()}{i+1}@example.com'
            phone = f'9{random.randint(100000000, 999999999)}'
            
            # Ensure uniqueness
            while User.objects.filter(email=email).exists():
                email = f'{first_name.lower()}.{last_name.lower()}{random.randint(100, 999)}@example.com'
            
            while User.objects.filter(phone=phone).exists():
                phone = f'9{random.randint(100000000, 999999999)}'
            
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'user_type': 4,  # Client
                }
            )
            
            if created:
                # Set password as 'password123' for all users
                user.set_password('password123')
                user.save()
                users_created += 1
                
                # Create a sample OTP for each user (for testing OTP login)
                OTP.objects.create(
                    phone=phone,
                    code='123456',
                    is_verified=False
                )
                
                self.stdout.write(f'Created user: {user.email} | Phone: {user.phone} | Password: password123')
        
        # Print summary with login credentials
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✅ Recharge Backend: Successfully created {users_created} client users'))
        self.stdout.write('\n📋 RECHARGE BACKEND LOGIN CREDENTIALS:')
        self.stdout.write('='*60)
        
        # Admin login
        self.stdout.write('\n👤 RECHARGE BACKEND ADMIN:')
        self.stdout.write(f'Email: admin@rechargebackend.com')
        self.stdout.write(f'Password: rechargebackend123')
        self.stdout.write(f'Phone: 9999999999')
        
        # Client users
        self.stdout.write('\n👥 CLIENT USERS:')
        self.stdout.write('All client users have password: password123')
        self.stdout.write('OTP for all phones: 123456')
        
        client_users = User.objects.filter(user_type=4)[:5]  # Show first 5 users
        for user in client_users:
            self.stdout.write(f'• {user.email} | Phone: {user.phone}')
        
        if client_users.count() > 5:
            self.stdout.write(f'... and {client_users.count() - 5} more users')
        
        self.stdout.write('\n🔐 AUTHENTICATION METHODS:')
        self.stdout.write('1. Email + Password login')
        self.stdout.write('2. Phone + OTP login (OTP: 123456 for testing)')
        
        self.stdout.write('\n📚 EXAMPLE API CALLS:')
        self.stdout.write('# Register new user:')
        self.stdout.write('POST /api/auth/signup/')
        self.stdout.write('\n# Email login:')
        self.stdout.write('POST /api/auth/login/email/')
        self.stdout.write('{"email": "admin@rechargebackend.com", "password": "rechargebackend123"}')
        self.stdout.write('\n# Generate OTP:')
        self.stdout.write('POST /api/auth/otp/generate/')
        self.stdout.write('{"phone": "9999999999"}')
        self.stdout.write('\n# Verify OTP:')
        self.stdout.write('POST /api/auth/otp/verify/')
        self.stdout.write('{"phone": "9999999999", "code": "123456"}')
        self.stdout.write('\n🌐 Visit Recharge Backend Swagger: http://localhost:8000/swagger/')
        self.stdout.write('='*60)