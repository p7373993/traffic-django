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
