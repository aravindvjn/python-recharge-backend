from django.core.management.base import BaseCommand
from plans.models import Provider, Plans
from decimal import Decimal

class Command(BaseCommand):
    help = 'Populate Recharge Backend database with sample providers and mobile recharge plans'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing plans and providers...')
            Plans.objects.all().delete()
            Provider.objects.all().delete()
            
        # Create Providers
        providers_data = [
            {'title': 'Airtel', 'is_active': True},
            {'title': 'Jio', 'is_active': True},
            {'title': 'Vi (Vodafone Idea)', 'is_active': True},
            {'title': 'BSNL', 'is_active': True},
            {'title': 'Aircel', 'is_active': False},
        ]
        
        providers = {}
        for provider_data in providers_data:
            provider, created = Provider.objects.get_or_create(
                title=provider_data['title'],
                defaults={'is_active': provider_data['is_active']}
            )
            providers[provider.title] = provider
            if created:
                self.stdout.write(f'Created provider: {provider.title}')
            else:
                self.stdout.write(f'Provider already exists: {provider.title}')

        # Create Plans
        plans_data = [
            # Airtel Plans
            {
                'provider': 'Airtel',
                'title': 'Airtel ₹199 Plan',
                'description': 'Unlimited calls, 1.5GB daily data for 28 days',
                'validity': 28,
                'amount': Decimal('199.00'),
                'identifier': 'AIR_199_28D',
                'is_active': True
            },
            {
                'provider': 'Airtel',
                'title': 'Airtel ₹399 Plan',
                'description': 'Unlimited calls, 2.5GB daily data for 28 days',
                'validity': 28,
                'amount': Decimal('399.00'),
                'identifier': 'AIR_399_28D',
                'is_active': True
            },
            {
                'provider': 'Airtel',
                'title': 'Airtel ₹599 Plan',
                'description': 'Unlimited calls, 2GB daily data for 56 days',
                'validity': 56,
                'amount': Decimal('599.00'),
                'identifier': 'AIR_599_56D',
                'is_active': True
            },
            {
                'provider': 'Airtel',
                'title': 'Airtel ₹999 Plan',
                'description': 'Unlimited calls, 3GB daily data for 84 days',
                'validity': 84,
                'amount': Decimal('999.00'),
                'identifier': 'AIR_999_84D',
                'is_active': True
            },
            
            # Jio Plans
            {
                'provider': 'Jio',
                'title': 'Jio ₹149 Plan',
                'description': 'Unlimited calls, 1GB daily data for 20 days',
                'validity': 20,
                'amount': Decimal('149.00'),
                'identifier': 'JIO_149_20D',
                'is_active': True
            },
            {
                'provider': 'Jio',
                'title': 'Jio ₹299 Plan',
                'description': 'Unlimited calls, 2GB daily data for 28 days',
                'validity': 28,
                'amount': Decimal('299.00'),
                'identifier': 'JIO_299_28D',
                'is_active': True
            },
            {
                'provider': 'Jio',
                'title': 'Jio ₹555 Plan',
                'description': 'Unlimited calls, 1.5GB daily data for 56 days',
                'validity': 56,
                'amount': Decimal('555.00'),
                'identifier': 'JIO_555_56D',
                'is_active': True
            },
            {
                'provider': 'Jio',
                'title': 'Jio ₹1299 Plan',
                'description': 'Unlimited calls, 2GB daily data for 84 days',
                'validity': 84,
                'amount': Decimal('1299.00'),
                'identifier': 'JIO_1299_84D',
                'is_active': True
            },
            
            # Vi Plans
            {
                'provider': 'Vi (Vodafone Idea)',
                'title': 'Vi ₹179 Plan',
                'description': 'Unlimited calls, 1GB daily data for 24 days',
                'validity': 24,
                'amount': Decimal('179.00'),
                'identifier': 'VI_179_24D',
                'is_active': True
            },
            {
                'provider': 'Vi (Vodafone Idea)',
                'title': 'Vi ₹359 Plan',
                'description': 'Unlimited calls, 2GB daily data for 28 days',
                'validity': 28,
                'amount': Decimal('359.00'),
                'identifier': 'VI_359_28D',
                'is_active': True
            },
            {
                'provider': 'Vi (Vodafone Idea)',
                'title': 'Vi ₹719 Plan',
                'description': 'Unlimited calls, 1.5GB daily data for 56 days',
                'validity': 56,
                'amount': Decimal('719.00'),
                'identifier': 'VI_719_56D',
                'is_active': True
            },
            
            # BSNL Plans
            {
                'provider': 'BSNL',
                'title': 'BSNL ₹97 Plan',
                'description': 'Unlimited calls, 2GB daily data for 18 days',
                'validity': 18,
                'amount': Decimal('97.00'),
                'identifier': 'BSNL_97_18D',
                'is_active': True
            },
            {
                'provider': 'BSNL',
                'title': 'BSNL ₹187 Plan',
                'description': 'Unlimited calls, 2GB daily data for 28 days',
                'validity': 28,
                'amount': Decimal('187.00'),
                'identifier': 'BSNL_187_28D',
                'is_active': True
            },
            {
                'provider': 'BSNL',
                'title': 'BSNL ₹997 Plan',
                'description': 'Unlimited calls, 3GB daily data for 180 days',
                'validity': 180,
                'amount': Decimal('997.00'),
                'identifier': 'BSNL_997_180D',
                'is_active': True
            },
        ]
        
        plans_created = 0
        for plan_data in plans_data:
            provider = providers[plan_data['provider']]
            plan, created = Plans.objects.get_or_create(
                identifier=plan_data['identifier'],
                defaults={
                    'provider': provider,
                    'title': plan_data['title'],
                    'description': plan_data['description'],
                    'validity': plan_data['validity'],
                    'amount': plan_data['amount'],
                    'is_active': plan_data['is_active']
                }
            )
            if created:
                plans_created += 1
                self.stdout.write(f'Created plan: {plan.title}')
            else:
                self.stdout.write(f'Plan already exists: {plan.title}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Recharge Backend database successfully populated with {len(providers)} providers and {plans_created} new plans!'
            )
        )