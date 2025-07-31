from django.db import models

# Create your models here.
class TravelHistory(models.Model):
    start = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    start_weather = models.TextField()
    destination_weather = models.TextField()  
    directions = models.TextField()
    time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.start} to {self.destination} - {self.time}"