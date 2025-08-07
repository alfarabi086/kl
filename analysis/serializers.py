# serializers.py
from rest_framework import serializers
from .models import WindDataFile, WindAnalysis, DistributionAnalysis, EnergyAnalysis

class WindDataFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = WindDataFile
        fields = ['id', 'original_name', 'uploaded_at', 'latitude', 'longitude', 
                 'start_time', 'end_time']

class WindAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = WindAnalysis
        fields = ['id', 'wind_data', 'year', 'created_at']

class DistributionAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = DistributionAnalysis
        fields = ['id', 'wind_analysis', 'distribution_type', 'parameters', 'created_at']

class EnergyAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnergyAnalysis
        fields = ['id', 'distribution_analysis', 'turbine_type', 'total_energy', 
                 'max_energy', 'load_factor', 'energy_distribution', 'created_at']