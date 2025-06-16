from django.core.management.base import BaseCommand
from traffic.models import Intersection
from traffic.utils.kml_parser import parse_kml_to_intersections  # ← 이게 핵심!

class Command(BaseCommand):
    help = 'Import intersections from KML file'

    def add_arguments(self, parser):
        parser.add_argument('kml_path', type=str, help='Path to the KML file')

    def handle(self, *args, **options):
        kml_path = options['kml_path']
        intersections = parse_kml_to_intersections(kml_path)

        created_count = 0
        for item in intersections:
            _, created = Intersection.objects.get_or_create(
                name=item['name'],
                latitude=item['latitude'],
                longitude=item['longitude']
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"{created_count} intersections inserted."))
