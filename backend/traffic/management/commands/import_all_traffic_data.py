from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from traffic.models import Intersection, TrafficVolume
import pandas as pd
import unicodedata
import re
from pathlib import Path
import difflib
import os
from datetime import datetime, time


class Command(BaseCommand):
    help = 'Import all traffic volumes from an Excel file by scanning all sheets and matching road pairs'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='Path to the Excel file')
        parser.add_argument('--dry-run', action='store_true', help='Dry run without saving to database')

    def handle(self, *args, **options):
        """엑셀 파일에서 교통량 데이터를 가져와 DB에 저장"""
        file_path = options['file']
        dry_run = options.get('dry_run', False)
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'파일을 찾을 수 없습니다: {file_path}'))
            return
        
        try:
            # 엑셀 파일 읽기 (모든 시트)
            df_dict = pd.read_excel(file_path, sheet_name=None)
            
            # 도로명과 교차로 매핑 정의
            intersection_mappings = {
                'Córdova': 'Simon Bolivar Avenue & Cordova Avenue',
                'Sucre': 'Simon Bolivar Avenue & Sucre Avenue', 
                'Paseo de los Andes': 'Simon Bolivar Avenue & Paseo de los Andes Avenue',
                'Del Río': 'Simon Bolivar Avenue & Del Rio Avenue',
                'Brasil': 'Simon Bolivar Avenue & Brasil Avenue',
                'Garzón': 'Garzon Avenue & Husares de Junin Avenue'
            }
            
            total_records = 0
            
            # 각 시트별로 처리
            for sheet_name, df in df_dict.items():
                self.stdout.write(f'\n=== 시트 "{sheet_name}" 처리 중 ===')
                
                # 교차로 이름 결정
                intersection_name = intersection_mappings.get(sheet_name)
                if not intersection_name:
                    self.stdout.write(self.style.WARNING(f'시트 "{sheet_name}"에 대한 교차로 매핑을 찾을 수 없습니다.'))
                    continue
                
                # 교차로 가져오기 또는 생성
                intersection, created = Intersection.objects.get_or_create(
                    name=intersection_name,
                    defaults={
                        'latitude': 0.0,  # 기본값
                        'longitude': 0.0,  # 기본값
                    }
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'새 교차로 생성: {intersection_name}'))
                else:
                    self.stdout.write(f'기존 교차로 사용: {intersection_name}')
                
                # 교통량 컬럼 식별 (DAY, Time, 15 minutos, Total 등 제외)
                traffic_columns = []
                for col in df.columns:
                    col_lower = str(col).lower()
                    if any(skip in col_lower for skip in ['day', 'time', 'minutos', 'total', 'divided', 'nan']):
                        continue
                    if '(' in str(col) and ')' in str(col):  # 방향 정보가 있는 컬럼
                        traffic_columns.append(col)
                
                self.stdout.write(f'교통량 컬럼: {traffic_columns}')
                
                # 각 교통량 컬럼별로 데이터 처리
                sheet_records = 0
                for col in traffic_columns:
                    # 방향 추출
                    direction = self.extract_direction(str(col))
                    if not direction:
                        self.stdout.write(self.style.WARNING(f'방향을 추출할 수 없습니다: {col}'))
                        continue
                    
                    # 각 행별로 데이터 처리
                    for idx, row in df.iterrows():
                        try:
                            # 날짜와 시간 파싱
                            day = row['DAY']
                            time_str = row['Time']
                            
                            # 날짜 처리
                            if pd.isna(day):
                                continue
                            
                            # 시간 처리 - 여러 형식 지원
                            if pd.isna(time_str):
                                continue
                            
                            # datetime 객체 생성
                            if isinstance(time_str, str):
                                try:
                                    time_obj = datetime.strptime(time_str, '%H:%M:%S').time()
                                except ValueError:
                                    try:
                                        time_obj = datetime.strptime(time_str, '%H:%M').time()
                                    except ValueError:
                                        continue
                            elif hasattr(time_str, 'time'):
                                time_obj = time_str.time()
                            else:
                                continue
                            
                            # 날짜와 시간 결합
                            if isinstance(day, str):
                                date_obj = datetime.strptime(day, '%Y-%m-%d').date()
                            else:
                                date_obj = day.date() if hasattr(day, 'date') else day
                            
                            dt = datetime.combine(date_obj, time_obj)
                            
                            # 교통량 값 추출
                            volume = row[col]
                            if pd.isna(volume) or volume == 0:
                                continue
                            
                            volume = float(volume)
                            
                            # 데이터베이스에 저장 (dry-run이 아닌 경우)
                            if not dry_run:
                                TrafficVolume.objects.create(
                                    intersection=intersection,
                                    datetime=dt,
                                    direction=direction,
                                    volume=volume,
                                    is_simulated=False
                                )
                            
                            sheet_records += 1
                            
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f'행 {idx} 처리 중 오류: {e}')
                            )
                            continue
                
                total_records += sheet_records
                self.stdout.write(
                    self.style.SUCCESS(f'시트 "{sheet_name}" 완료: {sheet_records}개 레코드')
                )
            
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f'Dry run 완료: 총 {total_records}개 레코드가 생성될 예정입니다.')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'데이터 가져오기 완료! 총 {total_records}개의 교통량 데이터가 저장되었습니다.')
                )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'오류 발생: {e}'))
            import traceback
            traceback.print_exc()

    def extract_direction(self, column_name):
        """컬럼명에서 방향 추출"""
        # 괄호 안의 방향 정보 추출
        match = re.search(r'\(([A-Za-z]{2,3})\)', column_name)
        if match:
            direction = match.group(1).upper()
            
            # 방향 표준화
            direction_mapping = {
                'NS': 'NS',  # North-South
                'SN': 'SN',  # South-North
                'WE': 'WE',  # West-East
                'EW': 'EW',  # East-West
                'OE': 'WE',  # Oeste-Este (West-East)
                'EO': 'EW',  # Este-Oeste (East-West)
            }
            
            return direction_mapping.get(direction, direction)
        
        return None 