from django.core.management.base import BaseCommand
from traffic.models import Intersection, TrafficVolume
import pandas as pd
import difflib
import re
import os
from datetime import datetime
import unicodedata

class Command(BaseCommand):
    help = '엑셀에서 교통량 데이터를 추출해 intersection 유사도 매칭 및 방향 변환 테스트'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='엑셀 파일 경로')
        parser.add_argument('--dry-run', action='store_true', help='DB 저장 없이 매칭 결과만 출력')

    def normalize_road(self, name):
        if not name:
            return ''
        # 대소문자, 악센트, 공백, 특수문자 제거
        name = str(name)
        name = unicodedata.normalize('NFKD', name)
        name = ''.join([c for c in name if not unicodedata.combining(c)])
        name = name.upper()
        # 접두사 제거
        for prefix in ['AV.', 'AV', 'JR.', 'JR', 'CA.', 'CA', 'CL.', 'CL']:
            if name.startswith(prefix + ' '):
                name = name[len(prefix)+1:]
            elif name.startswith(prefix):
                name = name[len(prefix):]
        # 불필요한 뒷부분(예: Distrito 등) 제거
        name = name.split('DISTRITO')[0].strip()
        name = name.split('CODIGO')[0].strip()
        name = name.split('RED')[0].strip()
        name = name.split('AÑO')[0].strip()
        name = name.replace('-', ' - ')
        name = re.sub(r'\s+', ' ', name)
        return name.strip()

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options.get('dry_run', False)
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'파일을 찾을 수 없습니다: {file_path}'))
            return

        # 시트명과 교차로 이름 매핑
        sheet_to_intersection = {
            'Córdova': 'AV. BOLIVAR - AV. GRAL. CORDOVA',
            'Sucre': 'AV. BOLIVAR - AV. ANTONIO JOSE DE SUCRE',
            'Paseo de los Andes': 'AV. BOLIVAR - AV. PASEO DE LOS ANDES',
            'Del Río': 'AV. BOLIVAR - AV. DEL RIO',
            'Brasil': 'AV. BRASIL - AV. BOLIVAR',
            'Garzón': 'AV. GRAL. GARZON - JR. HUSARES DE JUNIN',
        }
        intersections = list(Intersection.objects.all())
        intersection_dict = {i.name: i for i in intersections}

        df_dict = pd.read_excel(file_path, sheet_name=None)
        for sheet_name, df in df_dict.items():
            self.stdout.write(f'\n=== 시트: {sheet_name} ===')
            if sheet_name not in sheet_to_intersection:
                self.stdout.write(self.style.WARNING(f'시트명 매핑 없음: {sheet_name}'))
                continue
            intersection_name = sheet_to_intersection[sheet_name]
            intersection_obj = intersection_dict.get(intersection_name)
            if not intersection_obj:
                self.stdout.write(self.style.WARNING(f'Intersection 테이블에 없음: {intersection_name}'))
                continue
            traffic_cols = [col for col in df.columns if '(' in str(col) and ')' in str(col)]
            count = 0
            for idx, row in df.iterrows():
                day = row['DAY']
                time = row['Time']
                try:
                    dt = datetime.combine(pd.to_datetime(day).date(), pd.to_datetime(time).time())
                except Exception:
                    continue
                for col in traffic_cols:
                    if 'divided' in str(col).lower() or 'total' in str(col).lower():
                        continue
                    val = row[col]
                    if pd.isna(val):
                        continue
                    direction = re.search(r'\(([A-Za-z]+)\)', str(col))
                    if direction:
                        d = direction.group(1).upper()
                        if d in ['OE', 'EO']:
                            d = 'WE' if d == 'OE' else 'EW'
                        TrafficVolume.objects.create(
                            intersection=intersection_obj,
                            datetime=dt,
                            direction=d,
                            volume=int(val),
                            is_simulated=False
                        )
                        count += 1
            self.stdout.write(self.style.SUCCESS(f'  → {count}개 TrafficVolume 저장됨')) 