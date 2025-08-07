import netCDF4 as nc
import numpy as np
from datetime import datetime, timedelta
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from ..models import WindDataFile

class NetCDFProcessor:
    def __init__(self, file_path):
        # Convert to absolute path if needed
        self.file_path = os.path.abspath(file_path)
        self.dataset = None
        
    def process(self):
        """Process the NetCDF file and extract wind data"""
        try:
            # Use forward slashes for netCDF4 (it handles this internally)
            self.dataset = nc.Dataset(self.file_path.replace('\\', '/'))
            return self._extract_wind_data()
        except Exception as e:
            raise ValueError(f"Error processing NetCDF file: {str(e)}")
        finally:
            if self.dataset:
                self.dataset.close()
    
    def _extract_wind_data(self):
        """Extract wind components from NetCDF file"""
        # Get wind components (U and V components)
        u_wind = self._get_variable(['var165', 'u10', 'u_wind', 'wind_u'])
        v_wind = self._get_variable(['var166', 'v10', 'v_wind', 'wind_v'])
        
        # Calculate wind speed magnitude and direction
        wind_speed = np.sqrt(u_wind**2 + v_wind**2)
        wind_direction = np.arctan2(v_wind, u_wind) * 180 / np.pi
        
        # Convert wind direction to meteorological convention (0-360°, 0° = North)
        wind_direction = (90 - wind_direction) % 360
        
        # Get time data
        time_var = self.dataset.variables.get('time')
        if not time_var:
            raise ValueError("Time variable not found in NetCDF file")
            
        time_units = getattr(time_var, 'units', '')
        time_values = time_var[:]
        
        # Parse time
        time_data = self._parse_time(time_units, time_values)
        
        # Get coordinates without rounding (like MATLAB)
        lat = self._get_coordinate('latitude', 'lat')
        lon = self._get_coordinate('longitude', 'lon')
        
        return {
            'u_wind': u_wind,
            'v_wind': v_wind,
            'wind_speed': wind_speed,
            'wind_direction': wind_direction,
            'time_data': time_data,
            'latitude': lat,
            'longitude': lon
        }
    
    def _get_variable(self, possible_names):
        """Get variable by trying multiple possible names"""
        for name in possible_names:
            if name in self.dataset.variables:
                return self.dataset.variables[name][:]
        raise ValueError(f"Could not find any of {possible_names} in NetCDF file")
    
    def _get_coordinate(self, primary_name, alternate_name):
        """Get coordinate (latitude/longitude) - same as MATLAB approach"""
        if primary_name in self.dataset.variables:
            coord_value = float(self.dataset.variables[primary_name][:])
        elif alternate_name in self.dataset.variables:
            coord_value = float(self.dataset.variables[alternate_name][:])
        else:
            raise ValueError(f"Could not find {primary_name} or {alternate_name} in NetCDF file")
        
        # Round to 6 decimal places to match MATLAB display precision
        return round(coord_value, 6)
    
    def _parse_time(self, time_units, time_values):
        """Parse time values from NetCDF file"""
        if not time_units.startswith('hours since ') and not time_units.startswith('days since '):
            raise ValueError(f"Unsupported time units format: {time_units}")
            
        # Extract epoch
        epoch_str = time_units.split('since ')[1].replace('.0', '')
        try:
            epoch = datetime.strptime(epoch_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            epoch = datetime.strptime(epoch_str, '%Y-%m-%d')
        
        # Convert time values to datetime
        if time_units.startswith('hours since '):
            time_data = [epoch + timedelta(hours=float(t)) for t in time_values]
        else:  # days since
            time_data = [epoch + timedelta(days=float(t)) for t in time_values]
        
        return time_data

    def get_wind_stats(self):
        """Get basic wind statistics"""
        data = self.process()
        wind_speed = data['wind_speed']
        wind_direction = data['wind_direction']
        
        # Remove invalid values
        valid_speed = wind_speed[wind_speed > 0]
        valid_speed = valid_speed[~np.isnan(valid_speed)]
        
        if len(valid_speed) == 0:
            return None
            
        return {
            'mean_speed': float(np.mean(valid_speed)),
            'std_speed': float(np.std(valid_speed)),
            'min_speed': float(np.min(valid_speed)),
            'max_speed': float(np.max(valid_speed)),
            'median_speed': float(np.median(valid_speed)),
            'count': len(valid_speed),
            'mean_direction': float(np.mean(wind_direction[~np.isnan(wind_direction)])),
            'std_direction': float(np.std(wind_direction[~np.isnan(wind_direction)]))
        }