from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from traffic.models import Intersection, TrafficVolume
import pandas as pd
import unicodedata
import re
from pathlib import Path
import difflib

PREFIXES = [
    'AV', 'JR', 'CA', 'CL', 'PSJ', 'C A', 'CALLE', 'GRAL', 'GENERAL', 'JR', 'AVENIDA', 'JIRON', 'CALLE', 'PASEO', 'ANTIGUA', 'NUEVA', 'ALTURA', 'JR', 'CA', 'AV', 'PSJ', 'C.A.', 'JR.', 'CA.', 'AV.', 'PSJ.'
]

def normalize(text):
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)]).upper()

def normalize_col(col):
    col = unicodedata.normalize('NFKD', str(col))
    return ''.join([c for c in col if not unicodedata.combining(c)])

def normalize_road_name(name):
    # 유니코드 정규화, 대문자, 특수문자/악센트/마침표/공백 모두 제거
    name = unicodedata.normalize('NFKD', str(name))
    name = ''.join([c for c in name if not unicodedata.combining(c)])
    name = name.upper()
    name = re.sub(r'[^A-Z0-9\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    # 접두사 제거 (단어 앞/중간 모두)
    for prefix in PREFIXES:
        name = re.sub(rf'\b{prefix}\b', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def extract_road_names(*names):
    # 여러 이름(시트명, 컬럼명 등)에서 도로명 추출
    roads = []
    for name in names:
        # 괄호 앞 부분만 사용
        main = str(name).split('(')[0]
        # '-' 또는 '/'로 분리
        for part in re.split(r'[-/]', main):
            n = normalize_road_name(part)
            if n and re.match(r'^[A-Z0-9 ]+$', n):
                roads.append(n)
    return roads

def road_match(r1, r2):
    # r1, r2가 서로 포함(substring)되면 True
    return r1 in r2 or r2 in r1

def road_pair_match(roads1, roads2):
    # 두 도로쌍(set/list)이 서로 부분일치라도 모두 매칭되면 True
    if len(roads1) != 2 or len(roads2) != 2:
        return False
    return (road_match(roads1[0], roads2[0]) and road_match(roads1[1], roads2[1])) or \
           (road_match(roads1[0], roads2[1]) and road_match(roads1[1], roads2[0]))

def get_road_pair_from_excel(sheet, col):
    roads = extract_road_names(sheet, col)
    return [r for r in roads if r]

def get_road_pair_from_intersection(name):
    roads = extract_road_names(name)
    return [r for r in roads if r]

def find_matching_intersection(road1, road2):
    for intersection in Intersection.objects.all():
        roads = extract_all_road_names_from_intersection(intersection.name)
        matches1 = difflib.get_close_matches(road1, roads, n=1, cutoff=0.8)
        matches2 = difflib.get_close_matches(road2, roads, n=1, cutoff=0.8)
        if matches1 and matches2:
            return intersection
    return None


class Command(BaseCommand):
    help = 'Import all traffic volumes from an Excel file by scanning all sheets and matching road pairs'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='Path to the Excel file')

    def handle(self, *args, **options):
        excel_path = Path(options['file'])
        xls = pd.ExcelFile(excel_path)
        total_created = 0
        for sheet in xls.sheet_names:
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n📄 처리 중: 시트 '{sheet}'"))
            df = xls.parse(sheet)
            direction_cols = [col for col in df.columns if '(' in str(col)]
            if not direction_cols:
                self.stdout.write(self.style.WARNING(f"⚠ 방향 데이터 없음 → 스킵"))
                continue
            for col in direction_cols:
                excel_roads = get_road_pair_from_excel(sheet, col)
                if len(excel_roads) != 2:
                    continue
                matched = None
                for intersection in Intersection.objects.all():
                    intersection_roads = get_road_pair_from_intersection(intersection.name)
                    if len(intersection_roads) == 2 and road_pair_match(excel_roads, intersection_roads):
                        matched = intersection
                        break
                if not matched:
                    self.stdout.write(self.style.WARNING(f"❌ 매칭된 교차로 없음: {excel_roads}"))
                    continue
                self.stdout.write(self.style.SUCCESS(f"✅ 매칭된 교차로: {matched.name}"))
                records = []
                for _, row in df.iterrows():
                    date_str = str(row['DAY']).split(' ')[0]
                    time_str = str(row['Time'])
                    dt = parse_datetime(f"{date_str}T{time_str}")
                    m = re.search(r'\(([A-Z]+)\)', str(col))
                    direction = m.group(1) if m else None
                    volume = row[col]
                    if pd.isna(volume) or not direction:
                        continue
                    records.append(TrafficVolume(
                        intersection=matched,
                        datetime=dt,
                        direction=direction,
                        volume=int(volume),
                        is_simulated=False
                    ))
                TrafficVolume.objects.bulk_create(records)
                self.stdout.write(self.style.SUCCESS(f"🎉 {len(records)}건 저장 완료"))
                total_created += len(records)
        self.stdout.write(self.style.SUCCESS(f"\n✅ 전체 저장 완료: {total_created}건"))
