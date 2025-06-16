from django.core.management.base import BaseCommand
from traffic.models import Intersection
import re

class Command(BaseCommand):
    help = '교차로 name을 정규화하고, 도로가 2개가 아닌 교차로는 삭제'

    def handle(self, *args, **options):
        qs = Intersection.objects.all()
        cleaned = 0
        deleted = 0
        for i in qs:
            # 부가정보 제거
            n = re.sub(r'(Distrito:.*|Codigo de Red:.*|Red:.*|Año.*|Instalado:.*)', '', i.name)
            n = n.strip(' -')
            # 도로명 분리
            roads = [r.strip() for r in re.split(r'[-/]',' '.join(n.split())) if r.strip()]
            if len(roads) == 2:
                i.name = f'{roads[0]} - {roads[1]}'
                i.save()
                cleaned += 1
            else:
                i.delete()
                deleted += 1
        self.stdout.write(self.style.SUCCESS(f'정규화 완료: {cleaned}개, 삭제: {deleted}개')) 