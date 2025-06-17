# 교통 데이터 분석 프로젝트

## 프로젝트 설정 및 실행 방법

1. 가상환경 생성 및 활성화
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

2. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

3. 데이터베이스 설정
- `database_data` 디렉토리의 README.md 파일을 참고하여 데이터를 로드합니다.
- 데이터 로드 방법: `database_data/README.md` 파일 참조

4. Django 서버 실행
```bash
cd backend
python manage.py runserver
```

## API 엔드포인트

### 교차로 교통 데이터 조회
```
GET /api/traffic-data/intersection/{intersection_id}?start_time={start_time}&end_time={end_time}
```

예시:
```
GET /api/traffic-data/intersection/2717?start_time=2024-03-20T10:00:00&end_time=2024-03-20T11:00:00
```

## 데이터베이스 데이터 로드
데이터베이스에 데이터를 로드하려면 `database_data` 디렉토리의 README.md 파일을 참고하세요.
- 데이터 파일 위치: `database_data/traffic_data.json`
- 상세 로드 방법: `database_data/README.md` 참조
