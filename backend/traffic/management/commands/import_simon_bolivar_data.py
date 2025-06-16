import pandas as pd
from django.core.management.base import BaseCommand
from traffic.models import Intersection, TrafficVolume
from datetime import datetime, time
import os

class Command(BaseCommand):
    help = 'Simon Bolivar Avenue 교차로 데이터를 Excel에서 가져와서 데이터베이스에 저장합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='Excel 파일 경로')
        parser.add_argument('--dry-run', action='store_true', help='실제 저장하지 않고 미리보기만 실행')

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'파일을 찾을 수 없습니다: {file_path}'))
            return

        try:
            # Excel 파일 읽기
            df = pd.read_excel(file_path)
            self.stdout.write(f'Excel 파일 로드 완료: {len(df)} 행')
            
            # 교차로 생성 또는 가져오기
            intersection_name = "Simon Bolivar Avenue & Cordova Avenue"
            
            if not dry_run:
                intersection, created = Intersection.objects.get_or_create(
                    name=intersection_name,
                    defaults={
                        'latitude': -12.0464,  # Lima 위도 (예시)
                        'longitude': -77.0428  # Lima 경도 (예시)
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'새 교차로 생성: {intersection_name}'))
                else:
                    self.stdout.write(f'기존 교차로 사용: {intersection_name}')
            else:
                self.stdout.write(f'[DRY RUN] 교차로: {intersection_name}')

            # 방향 매핑
            direction_mapping = {
                'Av. Cordova (NS)': 'NS',      # North to South
                'Av. Cordova (SN)': 'SN',      # South to North  
                'Av. Bolivar (WE)': 'WE',      # West to East
                'Av. Bolivar (EW)': 'EW',      # East to West
            }

            traffic_volume_count = 0
            
            # 각 행을 처리
            for index, row in df.iterrows():
                try:
                    # 날짜와 시간 결합하여 datetime 생성
                    date_value = row['DAY']
                    time_value = row['Time']
                    
                    # 날짜가 이미 datetime 타입인지 확인
                    if isinstance(date_value, pd.Timestamp):
                        date_part = date_value.date()
                    else:
                        date_part = pd.to_datetime(date_value).date()
                    
                    # 시간 파싱 (HH:MM:SS 형식으로 처리)
                    if isinstance(time_value, str):
                        try:
                            # HH:MM:SS 형식 시도
                            time_part = datetime.strptime(time_value, '%H:%M:%S').time()
                        except ValueError:
                            # HH:MM 형식 시도
                            time_part = datetime.strptime(time_value, '%H:%M').time()
                    else:
                        # time 객체인 경우
                        time_part = time_value
                    
                    # datetime 결합
                    dt = datetime.combine(date_part, time_part)
                    
                    # 각 방향별로 교통량 데이터 저장
                    for column_name, direction_code in direction_mapping.items():
                        volume = int(row[column_name]) if pd.notna(row[column_name]) else 0
                        
                        if not dry_run:
                            TrafficVolume.objects.create(
                                intersection=intersection,
                                datetime=dt,
                                direction=direction_code,
                                volume=volume,
                                is_simulated=False
                            )
                        else:
                            self.stdout.write(f'[DRY RUN] {dt} - {direction_code}: {volume}')
                        
                        traffic_volume_count += 1
                
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'행 {index} 처리 중 오류: {str(e)}')
                    )
                    continue

            if not dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f'데이터 가져오기 완료! {traffic_volume_count}개의 교통량 데이터가 저장되었습니다.')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'[DRY RUN] 총 {traffic_volume_count}개의 교통량 데이터가 처리될 예정입니다.')
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'파일 처리 중 오류 발생: {str(e)}')) 