from rest_framework import serializers
from .models import Intersection, TotalTrafficVolume, TrafficVolume
from .models import Incident

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

class IncidentSerializer(serializers.ModelSerializer):
    intersection_name = serializers.CharField(source="intersection.name", read_only=True)
    latitude = serializers.FloatField(source="intersection.latitude", read_only=True)
    longitude = serializers.FloatField(source="intersection.longitude", read_only=True)

    class Meta:
        model = Incident
        fields = [
            "id",
            "incident_number",
            "ticket_number",
            "incident_type",
            "incident_detail_type",
            "location_name",
            "district",
            "managed_by",
            "assigned_to",
            "description",
            "operator",
            "status",
            "registered_at",
            "last_status_update",
            "day",
            "month",
            "year",
            "intersection",
            "intersection_name",
            "latitude",
            "longitude",
        ]