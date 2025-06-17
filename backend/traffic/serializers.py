from rest_framework import serializers
from .models import Intersection, TotalTrafficVolume, TrafficVolume

class IntersectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Intersection
        fields = ['id', 'name', 'latitude', 'longitude', 'created_at', 'updated_at']

class TrafficVolumeSerializer(serializers.ModelSerializer):
    intersection_name = serializers.CharField(source='intersection.name', read_only=True)

    class Meta:
        model = TrafficVolume
        fields = ['id', 'intersection', 'intersection_name', 'datetime', 'direction', 
                 'volume', 'is_simulated', 'created_at', 'updated_at'] 
        
class TotalTrafficVolumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TotalTrafficVolume
        fields = ['datetime', 'total_volume', 'average_speed']