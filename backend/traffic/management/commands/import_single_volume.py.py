import csv
import os
import pandas as pd
from django.core.management.base import BaseCommand
from traffic.models import Intersection, TrafficVolume
from datetime import datetime

class Command(BaseCommand):
    help = 'Import traffic volume data from CSV or Excel (xlsx)'

    def add_arguments(self, parser):
        parser.add_argument('data_file', type=str)
        parser.add_argument('--intersection', type=str, required=True, help='교차로 이름')

    def handle(self, *args, **options):
        intersection_name = options['intersection']
        intersection, _ = Intersection.objects.get_or_create(name=intersection_name, defaults={'latitude': 0, 'longitude': 0})
        data_file = options['data_file']
        ext = os.path.splitext(data_file)[-1].lower()
        if ext == '.csv':
            df = pd.read_csv(data_file)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(data_file)
        else:
            self.stdout.write(self.style.ERROR('지원하지 않는 파일 형식입니다.'))
            return
        # 컬럼명 표준화
        df.columns = [str(c).strip() for c in df.columns]
        for _, row in df.iterrows():
            date_str = row.get('FECHA') or row.get('Fecha')
            time_str = row.get('Horario') or row.get('Time')
            if not date_str or not time_str:
                continue
            try:
                dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            except Exception:
                continue
            # 방향별 볼륨 저장 (예시: EW, NS, SN, WE)
            direction_map = {
                'EW': row.get('PM3403-04', 0),
                'WE': row.get('PM3403-10', 0),
                'NS': row.get('PM3403-01', 0),
                'SN': row.get('PM3403-07', 0),
            }
            for direction, volume in direction_map.items():
                try:
                    volume = int(volume)
                except Exception:
                    volume = 0
                TrafficVolume.objects.create(
                    intersection=intersection,
                    datetime=dt,
                    direction=direction,
                    volume=volume,
                    is_simulated=False
                )
        self.stdout.write(self.style.SUCCESS('Import completed!')) 