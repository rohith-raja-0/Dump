from django.db import models

# Create your models here.

class ReadingManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().using('readings')

class plug_reading(models.Model):
    timestamp = models.DateTimeField()
    current_power = models.FloatField()
    today_runtime = models.IntegerField()
    today_energy = models.FloatField()
    month_runtime = models.IntegerField()
    month_energy = models.FloatField()
    voltage_mv = models.FloatField()
    current_ma = models.FloatField()
    energy_wh = models.FloatField()

    objects = ReadingManager()

    class Meta:
        managed = False
        db_table = 'plug_readings'



