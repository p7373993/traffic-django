# traffic/management/commands/import_incidents.py

import pandas as pd
import re
from django.core.management.base import BaseCommand
from traffic.models import Incident, Intersection
from datetime import datetime


class Command(BaseCommand):
    help = 'Import incident data from Excel and link with intersections'

    def handle(self, *args, **options):
        df = pd.read_excel('data/incidents/reporte_incidencias 23.04.2025.xls')

        # 열 이름 영어로 변환
        df.columns = df.columns.str.strip()

        df = df.rename(columns={
            'Nro': 'incident_number',
            'Ticket': 'ticket_number',
            'Incidencia': 'incident_type',
            'Tipo': 'incident_detail_type',
            'Cruce': 'location_name',
            'Distrito': 'district',
            'Administrado por': 'managed_by',
            'Asignado a': 'assigned_to',
            'Detalle': 'description',
            'Operador': 'operator',
            'Estado': 'status',
            'Fecha de registro': 'registered_at',
            'Fecha ultimo Estado': 'last_status_update',
            'Día': 'day',
            'Mes': 'month',
            'Año': 'year',
        })

        print("✅ 변환된 열 목록:", df.columns.tolist())

        # 기존 데이터 삭제
        Incident.objects.all().delete()

        # Intersection 전체 캐싱
        intersections = list(Intersection.objects.all())
        unmatched_locations = []

        def normalize_road_name(name: str) -> str:
            """도로명 접두사 제거 (AV., JR., CA. 등)"""
            return re.sub(r'^(av\.?|jr\.?|ca\.?|alameda)\s+', '', name.strip(), flags=re.IGNORECASE).lower()

        def match_intersection(location_name: str):
            try:
                road_parts = [normalize_road_name(part) for part in location_name.split("-")]
            except Exception:
                return None

            for inter in intersections:
                name = inter.name.lower()
                norm_inter_name = normalize_road_name(name)

                match_count = sum(1 for road in road_parts if road in norm_inter_name)
                if match_count >= 2:
                    return inter
            return None

        # 데이터 삽입
        for _, row in df.iterrows():
            intersection = match_intersection(row['location_name'])

            if intersection is None:
                unmatched_locations.append(row['location_name'])

            Incident.objects.create(
                incident_number=row['incident_number'],
                ticket_number=row['ticket_number'],
                incident_type=row['incident_type'],
                incident_detail_type=row['incident_detail_type'],
                location_name=row['location_name'],
                district=row['district'],
                managed_by=row['managed_by'],
                assigned_to=row['assigned_to'],
                description=row['description'],
                operator=row['operator'],
                status=row['status'],
                registered_at=row['registered_at'],
                last_status_update=row['last_status_update'],
                day=row['day'],
                month=row['month'],
                year=row['year'],
                intersection=intersection,
            )

        self.stdout.write(self.style.SUCCESS('✅ Incident data import 완료'))

        if unmatched_locations:
            self.stdout.write(self.style.WARNING(f'⚠️ 매칭 실패: {len(unmatched_locations)}건의 교차로를 찾을 수 없음'))
            for loc in unmatched_locations:
                self.stdout.write(f'   - {loc}')
        else:
            self.stdout.write(self.style.SUCCESS('🎉 모든 사건이 교차로와 성공적으로 매칭되었습니다.'))
