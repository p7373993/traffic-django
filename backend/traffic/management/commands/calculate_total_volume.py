from django.core.management.base import BaseCommand
from traffic.models import TrafficVolume, TotalTrafficVolume, Intersection
from datetime import datetime
from collections import defaultdict

class Command(BaseCommand):
    help = 'TrafficVolume에 존재하는 교차로만 대상으로 15분 단위 총량 및 평균 속도 계산 후 TotalTrafficVolume에 저장'

    def handle(self, *args, **options):
        # 기존 데이터 삭제
        TotalTrafficVolume.objects.all().delete()
        self.stdout.write("🧹 기존 TotalTrafficVolume 데이터 삭제 완료")

        # 실제 데이터가 존재하는 교차로 ID만 추출
        intersection_ids = TrafficVolume.objects.values_list('intersection_id', flat=True).distinct()
        intersections = Intersection.objects.filter(id__in=intersection_ids)

        for intersection in intersections:
            self.stdout.write(f"\n🛣️ 교차로: {intersection.name}")

            # 이 교차로에 대한 모든 TrafficVolume 가져오기 (1회 쿼리)
            all_volumes = TrafficVolume.objects.filter(intersection=intersection).order_by('datetime')

            # 15분 단위로 그룹화
            slot_dict = defaultdict(list)
            for v in all_volumes:
                slot_start = v.datetime.replace(minute=(v.datetime.minute // 15) * 15, second=0, microsecond=0)
                slot_dict[slot_start].append(v.volume)

            bulk_objects = []
            for slot_start, volume_list in slot_dict.items():
                total_volume = sum(volume_list)

                # 평균 속도 계산 (간단한 고정 로직)
                base_speed = 50.0
                if total_volume > 1000:
                    avg_speed = base_speed * 0.5
                elif total_volume > 500:
                    avg_speed = base_speed * 0.7
                else:
                    avg_speed = base_speed

                bulk_objects.append(TotalTrafficVolume(
                    intersection=intersection,
                    datetime=slot_start,
                    total_volume=total_volume,
                    average_speed=round(avg_speed, 2)
                ))

            # 일괄 저장
            TotalTrafficVolume.objects.bulk_create(bulk_objects)
            self.stdout.write(f"✅ 저장 완료: {len(bulk_objects)}건")
