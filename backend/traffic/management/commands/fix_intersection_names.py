from django.core.management.base import BaseCommand
from traffic.models import Intersection

class Command(BaseCommand):
    help = 'Fix intersection names by extracting only the road names'

    def handle(self, *args, **options):
        intersections = Intersection.objects.all()
        updated_count = 0

        for intersection in intersections:
            # ":" 이전의 부분만 추출
            if ':' in intersection.name:
                new_name = intersection.name.split(':')[0].strip()
                intersection.name = new_name
                intersection.save()
                updated_count += 1
                self.stdout.write(f'수정됨: {new_name}')

        self.stdout.write(self.style.SUCCESS(f'총 {updated_count}개의 교차로 이름이 수정되었습니다.')) 