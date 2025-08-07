# models.py
from django.db import models

class WindDataFile(models.Model):
    file = models.FileField(upload_to='wind_data/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    original_name = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.original_name

class WindAnalysis(models.Model):
    wind_data = models.ForeignKey(WindDataFile, on_delete=models.CASCADE)
    year = models.IntegerField()
    wind_speeds = models.JSONField()  # Stores filtered wind speeds for the year
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('wind_data', 'year')

class DistributionAnalysis(models.Model):
    wind_analysis = models.ForeignKey(WindAnalysis, on_delete=models.CASCADE)
    distribution_type = models.CharField(max_length=20, choices=[
        ('normal', 'Normal'),
        ('lognormal', 'Lognormal'),
        ('weibull', 'Weibull'),
        ('gumbel', 'Gumbel')
    ])
    parameters = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

class EnergyAnalysis(models.Model):
    distribution_analysis = models.ForeignKey(DistributionAnalysis, on_delete=models.CASCADE)
    turbine_type = models.CharField(max_length=20, choices=[
        ('bergey_excel_10', 'Bergey Excel 10'),
        ('bergey_excel_15', 'Bergey Excel 15'),
        ('cf_20', 'CF 20')
    ])
    total_energy = models.FloatField()
    max_energy = models.FloatField()
    load_factor = models.FloatField()
    energy_distribution = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)