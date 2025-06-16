from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IntersectionViewSet, TrafficVolumeViewSet

router = DefaultRouter()
router.register(r'intersections', IntersectionViewSet)
router.register(r'traffic-volumes', TrafficVolumeViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 