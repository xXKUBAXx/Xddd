from django.core.management.base import BaseCommand
import csv
from backend.models import primislaoDomains

class Command(BaseCommand):
    help = 'Updates domain categories from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file = options['csv_file']

        domain_category_mapping = {}
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                domain_name = row[0]
                category = row[1]
                domain_category_mapping[domain_name] = category

        for domain in primislaoDomains.objects.all():
            domain_name = domain.domain_name
            if domain_name in domain_category_mapping:
                domain.domain_category = domain_category_mapping[domain_name]
                domain.save()

        self.stdout.write(self.style.SUCCESS('Domain categories updated successfully.'))