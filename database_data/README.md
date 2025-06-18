# 교통 데이터베이스 백업

이 디렉토리에는 다음 테이블의 데이터가 포함되어 있습니다:
- traffic_intersection (교차로 정보)
- traffic_trafficvolume (교통량 데이터)
- total_traffic_volume (총 교통량 데이터)
- traffic_incident (사고/사건 데이터)

## 데이터 로드 방법

1. 프로젝트의 가상환경을 활성화합니다:
```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

2. 데이터베이스에 데이터를 로드합니다:
```bash
# 교통량 데이터 로드
python manage.py loaddata traffic_data.json

# 사고/사건 데이터 로드
python manage.py loaddata incident_data.json
```

## 주의사항
- 데이터를 로드하기 전에 데이터베이스가 비어있어야 합니다.
- 기존 데이터가 있다면 먼저 백업하시기 바랍니다.
- 데이터 로드 후에는 Django 서버를 재시작하는 것이 좋습니다. 