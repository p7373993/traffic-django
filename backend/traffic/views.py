from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.db.models import Sum, Avg
from .models import Intersection, TrafficVolume, TotalTrafficVolume
from .serializers import IntersectionSerializer, TrafficVolumeSerializer
import logging
import sys
from datetime import datetime, timedelta
from rest_framework import status
from django.utils import timezone

# 로깅 설정 수정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('django_log.txt', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)  # 콘솔에도 출력
    ]
)
logger = logging.getLogger(__name__)

# Create your views here.

class IntersectionViewSet(viewsets.ModelViewSet):
    queryset = Intersection.objects.all()
    serializer_class = IntersectionSerializer

    def list(self, request, *args, **kwargs):
        logger.info("교차로 목록 요청 받음")
        queryset = self.get_queryset()
        logger.info(f"조회된 교차로 수: {queryset.count()}")
        serializer = self.get_serializer(queryset, many=True)
        logger.info(f"직렬화된 데이터: {serializer.data}")
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def map_data(self, request):
        """지도 표시용 교차로 데이터"""
        try:
            intersections = Intersection.objects.all()
            logger.info(f"Found {intersections.count()} intersections")
            
            data = []
            for intersection in intersections:
                traffic_volumes = TrafficVolume.objects.filter(
                    intersection=intersection
                ).values('direction').annotate(
                    total_volume=Sum('volume')
                )
                
                intersection_data = {
                    'id': intersection.id,
                    'name': intersection.name,
                    'latitude': float(intersection.latitude),
                    'longitude': float(intersection.longitude),
                    'traffic_volumes': list(traffic_volumes)
                }
                data.append(intersection_data)
                logger.info(f"Processed intersection {intersection.id}")
            
            return Response(data)
        except Exception as e:
            logger.error(f"Error in map_data: {str(e)}")
            return Response({"error": str(e)}, status=500)

    @action(detail=True, methods=['get'])
    def traffic_volumes(self, request, pk=None):
        """특정 교차로의 교통량 데이터"""
        intersection = self.get_object()
        traffic_volumes = TrafficVolume.objects.filter(intersection=intersection)
        serializer = TrafficVolumeSerializer(traffic_volumes, many=True)
        return Response(serializer.data)

class TrafficVolumeViewSet(viewsets.ModelViewSet):
    queryset = TrafficVolume.objects.all()
    serializer_class = TrafficVolumeSerializer

    def list(self, request, *args, **kwargs):
        logger.info("교통량 데이터 요청 받음")
        queryset = self.get_queryset()
        logger.info(f"조회된 교통량 데이터 수: {queryset.count()}")
        serializer = self.get_serializer(queryset, many=True)
        logger.info(f"직렬화된 데이터: {serializer.data}")
        return Response(serializer.data)

    def get_queryset(self):
        queryset = TrafficVolume.objects.all()
        intersection_id = self.request.query_params.get('intersection', None)
        if intersection_id:
            queryset = queryset.filter(intersection_id=intersection_id)
        return queryset

@api_view(['GET'])
def get_intersection_traffic_data(request, intersection_id):
    print(f"API 호출됨 - 교차로 ID: {intersection_id}")  # 콘솔에 즉시 출력
    logger.info(f"교차로 교통 데이터 요청 받음 - 교차로 ID: {intersection_id}")
    
    try:
        # URL 파라미터에서 시작 시간과 종료 시간 가져오기
        start_time = request.GET.get('start_time')
        end_time = request.GET.get('end_time')
        print(f"요청된 시간 범위 - 시작: {start_time}, 종료: {end_time}")  # 콘솔에 즉시 출력
        logger.info(f"요청된 시간 범위 - 시작: {start_time}, 종료: {end_time}")

        if not start_time or not end_time:
            error_msg = "start_time과 end_time 파라미터가 필요합니다."
            print(error_msg)  # 콘솔에 즉시 출력
            logger.error(error_msg)
            return Response({'error': error_msg}, status=400)

        # 시간 형식 변환
        try:
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            print(f"변환된 시간 범위 - 시작: {start_time}, 종료: {end_time}")  # 콘솔에 즉시 출력
            logger.info(f"변환된 시간 범위 - 시작: {start_time}, 종료: {end_time}")
        except ValueError as e:
            error_msg = f"시간 형식이 잘못되었습니다: {str(e)}"
            print(error_msg)  # 콘솔에 즉시 출력
            logger.error(error_msg)
            return Response({'error': error_msg}, status=400)

        # 교차로 존재 여부 확인
        intersection_exists = Intersection.objects.filter(id=intersection_id).exists()
        print(f"교차로 존재 여부: {intersection_exists}")  # 콘솔에 즉시 출력
        logger.info(f"교차로 존재 여부: {intersection_exists}")

        if not intersection_exists:
            error_msg = f"교차로 ID {intersection_id}가 존재하지 않습니다."
            print(error_msg)  # 콘솔에 즉시 출력
            logger.error(error_msg)
            return Response({'error': error_msg}, status=404)

        # 해당 교차로의 교통 데이터 조회
        traffic_data = TotalTrafficVolume.objects.filter(
            intersection_id=intersection_id,
            datetime__range=(start_time, end_time)
        ).order_by('datetime')
        
        print(f"조회된 데이터 수: {traffic_data.count()}")  # 콘솔에 즉시 출력
        logger.info(f"조회된 데이터 수: {traffic_data.count()}")
        
        if traffic_data.count() == 0:
            warning_msg = "해당 조건에 맞는 데이터가 없습니다."
            print(warning_msg)  # 콘솔에 즉시 출력
            logger.warning(warning_msg)

        # 데이터 직렬화
        data = [{
            'intersection_id': item.intersection_id,
            'datetime': item.datetime,
            'total_volume': item.total_volume,
            'average_speed': item.average_speed
        } for item in traffic_data]

        print(f"응답 데이터: {data}")  # 콘솔에 즉시 출력
        logger.info(f"응답 데이터: {data}")
        return Response(data)
    except Exception as e:
        error_msg = f"에러 발생: {str(e)}"
        print(error_msg)  # 콘솔에 즉시 출력
        logger.error(error_msg, exc_info=True)
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
def get_all_intersections_traffic_data(request):
    try:
        # URL 파라미터에서 시간 가져오기
        time = request.GET.get('time')
        if not time:
            time = timezone.now()

        # 모든 교차로의 특정 시간대 교통 데이터 조회
        traffic_data = TotalTrafficVolume.objects.filter(
            timestamp=time
        ).order_by('intersection_id')

        # 데이터 직렬화
        data = [{
            'intersection_id': item.intersection_id,
            'timestamp': item.timestamp,
            'total_volume': item.total_volume
        } for item in traffic_data]

        return Response(data)
    except Exception as e:
        return Response({'error': str(e)}, status=400)
