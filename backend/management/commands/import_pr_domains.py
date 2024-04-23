import csv
from django.core.management.base import BaseCommand
from backend.models import primislaoDomains
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Imports domains from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                domain_name = row['url']
                server_name = row['server']

                try:
                    primislaoDomains.objects.create(
                        domain_name=domain_name,
                        server_name=server_name
                    )
                except IntegrityError:
       
                    existing_domain = primislaoDomains.objects.get(server_name=server_name)
                    self.stdout.write(self.style.WARNING(
                        f"Skipping duplicate record: {domain_name} - {server_name}. "
                        f"Existing record: {existing_domain.domain_name} - {existing_domain.server_name}"
                    ))

        self.stdout.write(self.style.SUCCESS('Domains imported successfully.'))