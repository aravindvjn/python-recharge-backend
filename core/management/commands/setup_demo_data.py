from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Setup complete Recharge Backend demo data - providers, plans, and users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of client users to create (default: 10)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing data before setup',
        )

    def handle(self, *args, **options):
        self.stdout.write('🚀 Setting up demo data for Recharge Backend API...')
        self.stdout.write('='*70)
        
        # Setup plans and providers
        self.stdout.write('\n📋 Setting up mobile providers and recharge plans...')
        call_command('populate_plans', clear=options['clear'])
        
        # Setup users
        self.stdout.write('\n👥 Setting up Recharge Backend demo users...')
        call_command('create_users', count=options['users'], clear=options['clear'])
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('✅ Recharge Backend demo data setup completed successfully!'))
        
        self.stdout.write('\n🌐 Next steps:')
        self.stdout.write('1. Start Recharge Backend server: uv python manage.py runserver')
        self.stdout.write('2. Visit Swagger docs: http://localhost:8000/swagger/')
        self.stdout.write('3. Test authentication with provided credentials')
        self.stdout.write('4. Browse and purchase mobile recharge plans')
        
        self.stdout.write('\n📖 Quick Recharge Backend API Test:')
        self.stdout.write('# Login to get JWT token:')
        self.stdout.write('curl -X POST http://localhost:8000/api/auth/login/email/ \\')
        self.stdout.write('  -H "Content-Type: application/json" \\')
        self.stdout.write('  -d \'{"email": "admin@rechargebackend.com", "password": "rechargebackend123"}\'')
        
        self.stdout.write('\n# List mobile recharge plans:')
        self.stdout.write('curl -X GET http://localhost:8000/api/plans/ \\')
        self.stdout.write('  -H "Authorization: Bearer <your_jwt_token>"')
        
        self.stdout.write('\n🎯 Happy recharging with Recharge Backend!')
        self.stdout.write('='*70)