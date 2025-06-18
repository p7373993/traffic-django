from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IntersectionViewSet, TrafficVolumeViewSet, get_intersection_traffic_data, get_all_intersections_traffic_data, IncidentViewSet

router = DefaultRouter()
router.register(r'intersections', IntersectionViewSet)
router.register(r'traffic-volumes', TrafficVolumeViewSet)
router.register(r'incidents', IncidentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # 교차로 교통 데이터 API             
    path('traffic-data/intersection/<int:intersection_id>/', get_intersection_traffic_data, name='get_intersection_traffic_data'),
    path('traffic-data/intersections/', get_all_intersections_traffic_data, name='get_all_intersections_traffic_data'),
] 