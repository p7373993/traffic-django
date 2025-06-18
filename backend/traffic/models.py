from django.db import models

# Create your models here.

class Intersection(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class TrafficVolume(models.Model):
    DIRECTION_CHOICES = [
        ('NS', 'North to South'),
        ('SN', 'South to North'),
        ('EW', 'East to West'),
        ('WE', 'West to East'),
    ]

    intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE, related_name='traffic_volumes')
    datetime = models.DateTimeField()
    direction = models.CharField(max_length=2, choices=DIRECTION_CHOICES)
    volume = models.IntegerField()
    is_simulated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.intersection.name} - {self.datetime} - {self.direction}"

    class Meta:
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['intersection', 'datetime']),
            models.Index(fields=['direction']),
        ]

class TotalTrafficVolume(models.Model):
    intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE)
    datetime = models.DateTimeField()
    total_volume = models.IntegerField()
    average_speed = models.FloatField()

    class Meta:
        db_table = 'total_traffic_volume'
        indexes = [
            models.Index(fields=['intersection', 'datetime']),
        ]

    def __str__(self):
        return f"{self.intersection.name} - {self.datetime}: {self.total_volume}대, {self.average_speed}km/h"


# traffic/models.py

class Incident(models.Model):
    incident_number = models.IntegerField()
    ticket_number = models.IntegerField()
    incident_type = models.CharField(max_length=100)
    incident_detail_type = models.CharField(max_length=100)
    location_name = models.CharField(max_length=200)
    district = models.CharField(max_length=100)
    managed_by = models.CharField(max_length=100)
    assigned_to = models.CharField(max_length=100)
    description = models.TextField()
    operator = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    registered_at = models.DateTimeField()
    last_status_update = models.DateTimeField()
    day = models.IntegerField()
    month = models.IntegerField()
    year = models.IntegerField()
    intersection = models.ForeignKey("Intersection", on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.ticket_number} - {self.location_name}"
