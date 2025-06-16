from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from .models import Intersection, TrafficVolume
from .serializers import IntersectionSerializer, TrafficVolumeSerializer
import logging
import sys

# 로깅 설정 수정
logging.basicConfig(
    filename='django_log.txt',
    filemode='w',
    encoding='utf-8',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
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
