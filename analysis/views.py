import numpy as np
import os
import tempfile
import netCDF4 as nc
from scipy.stats import norm, lognorm, weibull_min, gumbel_r, kstest, chi2
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from datetime import datetime
from scipy.integrate import quad
from .services.file_processing import NetCDFProcessor
from scipy.interpolate import interp1d
from .services.distribution import DistributionAnalyzer
from rest_framework.generics import ListAPIView, RetrieveAPIView
from .models import WindDataFile, WindAnalysis, DistributionAnalysis, EnergyAnalysis
from .serializers import (
    WindDataFileSerializer, 
    WindAnalysisSerializer,
    DistributionAnalysisSerializer,
    EnergyAnalysisSerializer
)

class UploadNetCDFView(APIView):
    parser_classes = [MultiPartParser]
    
    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Save the file to persistent storage
            wind_file = WindDataFile(
                file=file_obj,
                original_name=file_obj.name
            )
            wind_file.save()
            
            # Process the file
            processor = NetCDFProcessor(wind_file.file.path)
            result = processor.process()
            
            # Store processing results in the model without rounding
            wind_file.latitude = result['latitude']
            wind_file.longitude = result['longitude']
            wind_file.start_time = result['time_data'][0]
            wind_file.end_time = result['time_data'][-1]
            wind_file.save()
            
            # Get time range
            years = list({t.year for t in result['time_data']})
            
            return Response({
                'message': 'File processed successfully',
                'file_id': wind_file.id,
                'file_name': wind_file.original_name,
                'file_path': wind_file.file.url if hasattr(wind_file.file, 'url') else wind_file.file.path,
                'latitude': f"{result['latitude']:.6f}",  # Format dengan 6 digit decimal seperti MATLAB
                'longitude': f"{result['longitude']:.6f}", 
                'years': sorted(years),
                'time_range': {
                    'start': result['time_data'][0].isoformat(),
                    'end': result['time_data'][-1].isoformat()
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            if 'wind_file' in locals():
                wind_file.delete()  # Clean up if processing fails
            return Response(
                {'error': f'Error processing file: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
class WindStatisticsView(APIView):
    def post(self, request):
        file_id = request.data.get('file_id')
        year = request.data.get('year')
        
        if not file_id or not year:
            return Response(
                {'error': 'File ID and year are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            year = int(year)
            wind_file = WindDataFile.objects.get(pk=file_id)
            
            # Process NetCDF file
            processor = NetCDFProcessor(wind_file.file.path)
            result = processor.process()
            
            time_data = result['time_data']
            # IMPORTANT: Use wind_speed, NOT wind_direction!
            wind_speed = result['wind_speed']  # This is the magnitude
            wind_direction = result['wind_direction']  # This is the direction
            
            # Filter by year
            mask = np.array([t.year == year for t in time_data])
            filtered_wind_speed = wind_speed[mask]
            filtered_wind_direction = wind_direction[mask]
            
            # Remove invalid values for wind speed
            valid_speed = filtered_wind_speed[filtered_wind_speed > 0]
            valid_speed = valid_speed[~np.isnan(valid_speed)]
            
            # Remove invalid values for wind direction
            valid_direction = filtered_wind_direction[~np.isnan(filtered_wind_direction)]
            
            if len(valid_speed) == 0:
                return Response(
                    {'error': 'No valid wind speed data found for the specified year'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculate statistics for wind speed (like MATLAB)
            wind_speed_stats = {
                'mean': float(np.mean(valid_speed)),
                'std': float(np.std(valid_speed)),
                'max': float(np.max(valid_speed)),
                'min': float(np.min(valid_speed)),
                'median': float(np.median(valid_speed)),
                'count': len(valid_speed)
            }
            
            # Calculate statistics for wind direction (optional)
            wind_direction_stats = {
                'mean': float(np.mean(valid_direction)),
                'std': float(np.std(valid_direction)),
                'max': float(np.max(valid_direction)),
                'min': float(np.min(valid_direction)),
                'count': len(valid_direction)
            }
            
            # Get coordinates
            lat = result['latitude']
            lon = result['longitude']
            
            # Get year range from time data
            years = list(set([t.year for t in time_data]))
            year_range = {
                'min_year': min(years),
                'max_year': max(years),
                'available_years': sorted(years)
            }
            
            return Response({
                'file_id': file_id,
                'year': year,
                'coordinates': {
                    'latitude': lat,
                    'longitude': lon
                },
                'year_range': year_range,
                'wind_speed_statistics': wind_speed_stats,  # This is what you want
                'wind_direction_statistics': wind_direction_stats,  # Additional info
                'data_info': {
                    'total_records': len(time_data),
                    'filtered_records': len(valid_speed),
                    'unit': 'm/s'  # Make sure unit is clear
                }
            })
            
        except WindDataFile.DoesNotExist:
            return Response(
                {'error': 'File not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error processing file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class WindDistributionView(APIView):
    def post(self, request):
        file_id = request.data.get('file_id')
        year = request.data.get('year')
        
        if not file_id or not year:
            return Response(
                {'error': 'File ID and year are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            year = int(year)
            wind_file = WindDataFile.objects.get(pk=file_id)
            
            # Get or create wind analysis
            wind_analysis, created = WindAnalysis.objects.get_or_create(
                wind_data=wind_file,
                year=year,
                defaults={
                    'wind_speeds': self._get_wind_speeds(wind_file, year)
                }
            )
            
            wind_speeds = np.array(wind_analysis.wind_speeds)
            
            # Remove invalid values (zeros, negatives, NaN)
            wind_speeds = wind_speeds[wind_speeds > 0]
            wind_speeds = wind_speeds[~np.isnan(wind_speeds)]
            
            if len(wind_speeds) == 0:
                return Response(
                    {'error': 'No valid wind speed data found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Fit distributions
            analyzer = DistributionAnalyzer(wind_speeds)
            analyzer.analyze_all()
            
            # Generate data for plotting (equivalent to MATLAB linspace and pdf)
            x = np.linspace(min(wind_speeds), max(wind_speeds), 100)
            distributions = {}
            
            # Add distributions that were successfully fitted
            for dist_name, dist_data in analyzer.results.items():
                distributions[dist_name] = {
                    'x': x.tolist(),
                    'y': dist_data['pdf'](x).tolist(),
                    'parameters': dist_data['params']
                }
            
            # Add histogram data
            distributions['histogram'] = {
                'values': wind_speeds.tolist()
            }
            
            # Save distributions to database
            for dist_name, dist_data in analyzer.results.items():
                DistributionAnalysis.objects.update_or_create(
                    wind_analysis=wind_analysis,
                    distribution_type=dist_name,
                    defaults={
                        'parameters': dist_data['params']
                    }
                )
            
            return Response({
                'file_id': file_id,
                'year': year,
                'distributions': distributions,
                'data_stats': {
                    'count': len(wind_speeds),
                    'min': float(np.min(wind_speeds)),
                    'max': float(np.max(wind_speeds)),
                    'mean': float(np.mean(wind_speeds)),
                    'std': float(np.std(wind_speeds))
                }
            })
            
        except WindDataFile.DoesNotExist:
            return Response(
                {'error': 'File not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error analyzing distributions: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # Ensure identical data preprocessing to MATLAB
    # In WindDistributionView._get_wind_speeds()
    def _get_wind_speeds(self, wind_file, year):
        processor = NetCDFProcessor(wind_file.file.path)
        result = processor.process()
        
        time_data = result['time_data']
        wind_speed = result['wind_speed']
        
        # Filter by year and remove invalid values
        mask = np.array([t.year == year for t in time_data])
        filtered_wind_speed = wind_speed[mask]
        filtered_wind_speed = filtered_wind_speed[filtered_wind_speed > 0]
        filtered_wind_speed = filtered_wind_speed[~np.isnan(filtered_wind_speed)]
        
        # Convert to float32 to match MATLAB's default precision
        return filtered_wind_speed.astype(np.float32).tolist()

class BestDistributionView(APIView):
    def post(self, request):
        file_id = request.data.get('file_id')
        year = request.data.get('year')
        
        if not file_id or not year:
            return Response(
                {'error': 'File ID and year are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            year = int(year)
            wind_file = WindDataFile.objects.get(pk=file_id)
            wind_analysis = WindAnalysis.objects.get(wind_data=wind_file, year=year)
            
            # Get wind speeds and validate
            wind_speeds = np.array(wind_analysis.wind_speeds)
            self.data = wind_speeds  # Store for later use
            
            # Remove invalid values (keep zeros for normal and gumbel)
            wind_speeds_clean = wind_speeds[wind_speeds >= 0]
            
            if len(wind_speeds_clean) == 0:
                return Response(
                    {'error': 'No valid wind speed values found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Fit distributions using MATLAB-compatible methods
            distributions = self._fit_distributions_matlab_style(wind_speeds_clean)
            
            # Calculate metrics with MATLAB-compatible methods
            aic_values = self._calculate_aic_values_matlab(distributions)
            chi2_values = self._calculate_chi_square_matlab_style(wind_speeds_clean, distributions)
            ks_values = self._calculate_ks_matlab_style(wind_speeds_clean, distributions)
            
            # Prepare response data
            response_data = {
                'file_id': file_id,
                'year': year,
                'data_points_used': len(wind_speeds_clean),
                'original_data_points': len(wind_speeds),
                'aic': {
                    'values': {k: float(v) if not np.isinf(v) else float('inf') 
                              for k, v in aic_values.items()},
                    'best': min(aic_values, key=aic_values.get) if aic_values else None
                },
                'chi_square': {
                    'values': {k: float(v) if not np.isinf(v) else float('inf')
                               for k, v in chi2_values.items()},
                    'best': min(chi2_values, key=chi2_values.get) if chi2_values else None
                },
                'kolmogorov_smirnov': {
                    'values': {k: float(v) for k, v in ks_values.items()},
                    'best': max(ks_values, key=ks_values.get) if ks_values else None
                },
                'distributions': {
                    dist_name: {
                        'scipy_params': dist_data['params'],
                        'matlab_params': dist_data.get('matlab_params', {})
                    }
                    for dist_name, dist_data in distributions.items()
                }
            }
            
            return Response(response_data)
            
        except (WindDataFile.DoesNotExist, WindAnalysis.DoesNotExist):
            return Response(
                {'error': 'File or analysis not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error determining best distribution: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _fit_distributions_matlab_style(self, data):
        """Fit distributions using MATLAB-compatible methods"""
        distributions = {}
        
        # Normal distribution
        distributions['normal'] = self._fit_normal(data)
        
        # Lognormal distribution
        distributions['lognormal'] = self._fit_lognormal(data)
        
        # Weibull distribution
        distributions['weibull'] = self._fit_weibull(data)
        
        # Gumbel distribution - using MATLAB method
        distributions['gumbel'] = self._fit_gumbel_matlab_style(data)
        
        return {k: v for k, v in distributions.items() if v is not None}

    def _fit_normal(self, data):
        try:
            loc, scale = norm.fit(data)
            return {
                'params': (loc, scale),
                'matlab_params': {
                    'mu': loc,
                    'sigma': scale
                },
                'num_params': 2,
                'log_likelihood': np.sum(norm.logpdf(data, loc, scale)),
                'pdf': lambda x: norm.pdf(x, loc, scale),
                'cdf': lambda x: norm.cdf(x, loc, scale)
            }
        except Exception as e:
            print(f"Normal distribution fitting failed: {e}")
            return None

    def _fit_lognormal(self, data):
        try:
            positive_data = data[data > 0]
            if len(positive_data) == 0:
                return None
                
            s, loc, scale = lognorm.fit(positive_data, floc=0)
            mu = np.log(scale)
            sigma = s
            
            return {
                'params': (s, loc, scale),
                'matlab_params': {
                    'mu': mu,
                    'sigma': sigma
                },
                'num_params': 2,
                'log_likelihood': np.sum(lognorm.logpdf(positive_data, s, loc, scale)),
                'pdf': lambda x: lognorm.pdf(x, s, loc, scale),
                'cdf': lambda x: lognorm.cdf(x, s, loc, scale)
            }
        except Exception as e:
            print(f"Lognormal distribution fitting failed: {e}")
            return None

    def _fit_weibull(self, data):
        try:
            positive_data = data[data > 0]
            if len(positive_data) == 0:
                return None
                
            c, loc, scale = weibull_min.fit(positive_data, floc=0)
            return {
                'params': (c, loc, scale),
                'matlab_params': {
                    'a': scale,
                    'b': c
                },
                'num_params': 2,
                'log_likelihood': np.sum(weibull_min.logpdf(positive_data, c, loc, scale)),
                'pdf': lambda x: weibull_min.pdf(x, c, loc, scale),
                'cdf': lambda x: weibull_min.cdf(x, c, loc, scale)
            }
        except Exception as e:
            print(f"Weibull distribution fitting failed: {e}")
            return None

    def _fit_gumbel_matlab_style(self, data):
        """Calculate Gumbel parameters using MATLAB's Method of Moments"""
        try:
            # MATLAB's exact calculation method
            sigma = np.std(data, ddof=1) * np.sqrt(6) / np.pi  # scale parameter
            mu = np.mean(data) - 0.5772156649015329 * sigma    # Euler-Mascheroni constant
            
            return {
                'params': (mu, sigma),
                'matlab_params': {
                    'mu': mu,
                    'sigma': sigma
                },
                'num_params': 2,
                'log_likelihood': np.sum(gumbel_r.logpdf(data, loc=mu, scale=sigma)),
                'pdf': lambda x: gumbel_r.pdf(x, loc=mu, scale=sigma),
                'cdf': lambda x: gumbel_r.cdf(x, loc=mu, scale=sigma)
            }
        except Exception as e:
            print(f"Gumbel distribution fitting failed: {e}")
            return None

    def _calculate_aic_values_matlab(self, distributions):
        aic_values = {}
        
        for dist_name, dist_data in distributions.items():
            if not dist_data:
                aic_values[dist_name] = np.inf
                continue
                
            # MATLAB's AIC calculation: 2*Np + 2*NLogL
            k = dist_data['num_params']
            nlogl = -dist_data['log_likelihood']
            aic_values[dist_name] = 2 * k + 2 * nlogl
                
        return aic_values
    
    def _calculate_chi_square_matlab_style(self, data, distributions):
        chi2_values = {}
        counts, bin_edges = np.histogram(data, bins=10, density=False)
        n = len(data)
        
        for dist_name, dist_data in distributions.items():
            if not dist_data or dist_data['cdf'] is None:
                chi2_values[dist_name] = float('inf')
                continue
                
            try:
                cdf_values = dist_data['cdf'](bin_edges)
                expected = n * np.diff(cdf_values)
                expected = np.where(expected < 1, 1, expected)  # Avoid division by zero
                chi2 = np.sum((counts - expected)**2 / expected)
                chi2_values[dist_name] = chi2
            except Exception as e:
                print(f"Chi-square failed for {dist_name}: {str(e)}")
                chi2_values[dist_name] = float('inf')
        
        return chi2_values
    
    def _calculate_ks_matlab_style(self, data, distributions):
        ks_values = {}
        
        for dist_name, dist_data in distributions.items():
            if not dist_data or dist_data['cdf'] is None:
                ks_values[dist_name] = 0.0
                continue
                
            try:
                if dist_name in ['lognormal', 'weibull']:
                    test_data = data[data > 0]
                    if len(test_data) == 0:
                        ks_values[dist_name] = 0.0
                        continue
                else:
                    test_data = data
                    
                _, p_value = kstest(test_data, dist_data['cdf'])
                ks_values[dist_name] = p_value
            except Exception as e:
                print(f"KS test failed for {dist_name}: {str(e)}")
                ks_values[dist_name] = 0.0
        
        return ks_values

class DistributionParametersView(APIView):
    def post(self, request):
        file_id = request.data.get('file_id')
        year = request.data.get('year')
        
        if not file_id or not year:
            return Response(
                {'error': 'File ID and year are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            year = int(year)
            wind_file = WindDataFile.objects.get(pk=file_id)
            wind_analysis = WindAnalysis.objects.get(wind_data=wind_file, year=year)
            
            # Get wind speeds
            wind_speeds = np.array(wind_analysis.wind_speeds)
            wind_speeds = wind_speeds[wind_speeds >= 0]  # Remove negative values
            
            # Analyze distributions
            analyzer = DistributionAnalyzer(wind_speeds)
            analyzer.analyze_all()
            
            # Prepare response with MATLAB-style parameters
            response_data = {
                'file_id': file_id,
                'year': year,
                'distributions': {}
            }
            
            for dist_name, dist_data in analyzer.results.items():
                response_data['distributions'][dist_name] = {
                    'scipy_params': dist_data['params'],
                    'matlab_params': dist_data.get('matlab_params', {})
                }
            
            return Response(response_data)
            
        except (WindDataFile.DoesNotExist, WindAnalysis.DoesNotExist):
            return Response(
                {'error': 'File or analysis not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error getting distribution parameters: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
class EnergyPotentialView(APIView):
    def post(self, request):
        file_id = request.data.get('file_id')
        year = request.data.get('year')
        turbine_type = request.data.get('turbine_type', 'bergey_excel_10')
        distribution_type = request.data.get('distribution_type', 'weibull')
        
        if not file_id or not year:
            return Response(
                {'error': 'File ID and year are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            year = int(year)
            wind_file = WindDataFile.objects.get(pk=file_id)
            wind_analysis = WindAnalysis.objects.get(wind_data=wind_file, year=year)
            dist_analysis = DistributionAnalysis.objects.get(
                wind_analysis=wind_analysis,
                distribution_type=distribution_type
            )
            
            wind_speeds = np.array(wind_analysis.wind_speeds)
            
            # Get distribution function
            analyzer = DistributionAnalyzer(wind_speeds)
            analyzer.analyze_all()
            pdf_func = analyzer.results[distribution_type]['pdf']
            
            # Select turbine
            turbine_curves = {
                'bergey_excel_10': {
                    'curve': np.array([
                        [0, 0], [1, 0], [2, 0], [3, 0.1], [4, 0.4], [5, 0.85], 
                        [6, 1.51], [7, 2.4], [8, 3.6], [9, 5.07], [10, 6.86], 
                        [11, 8.86], [12, 10.89], [13, 12.02], [14, 12.4], 
                        [15, 12.4], [16, 12.4]
                    ]),
                    'rated_power': 8.86
                },
                'bergey_excel_15': {
                    'curve': np.array([
                        [0, 0], [1, 0], [2, 0], [3, 0.11], [4, 0.68], [5, 2.07], 
                        [6, 3.82], [7, 6.09], [8, 8.5], [9, 11.27], [10, 13.66], 
                        [11, 15.61], [12, 16.88], [13, 18.21], [14, 19.1], 
                        [15, 20.25], [16, 20.25], [17, 20.25]
                    ]),
                    'rated_power': 15.61
                },
                'cf_20': {
                    'curve': np.array([
                        [0, 0], [1, 0], [2, 0], [3, 0], [4, 0.70], [5, 2.07], 
                        [6, 3.92], [7, 6.72], [8, 10.59], [9, 14.89], [10, 18.94], 
                        [11, 20.08], [12, 20.08], [13, 20.08], [14, 20.08], 
                        [15, 20.08], [16, 20.08], [17, 20.08], [18, 20.08]
                    ]),
                    'rated_power': 20.08
                }
            }
            
            try:
                turbine = turbine_curves[turbine_type]
            except KeyError:
                return Response(
                    {'error': 'Invalid turbine type'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculate energy potential
            max_speed = np.ceil(np.max(wind_speeds))
            bin_edges = np.arange(0, max_speed + 1, 1)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            
            # Calculate probabilities
            probabilities = []
            for i in range(len(bin_edges) - 1):
                prob, _ = quad(pdf_func, bin_edges[i], bin_edges[i+1])
                probabilities.append(prob)
            
            # Interpolate power curve
            power_interp = interp1d(
                turbine['curve'][:, 0], 
                turbine['curve'][:, 1], 
                kind='linear', 
                fill_value='extrapolate'
            )
            
            power_outputs = power_interp(bin_centers)
            
            # Calculate energy
            hours_per_year = 8760
            hours_in_bins = np.array(probabilities) * hours_per_year
            energy_per_bin = hours_in_bins * power_outputs
            total_energy = np.sum(energy_per_bin)
            max_energy = turbine['rated_power'] * hours_per_year
            load_factor = (total_energy / max_energy) * 100
            
            # Prepare response
            energy_distribution = []
            for i in range(len(bin_edges) - 1):
                energy_distribution.append({
                    'bin_start': float(bin_edges[i]),
                    'bin_end': float(bin_edges[i+1]),
                    'energy': float(energy_per_bin[i])
                })
            
            # Save energy analysis
            energy_analysis = EnergyAnalysis.objects.create(
                distribution_analysis=dist_analysis,
                turbine_type=turbine_type,
                total_energy=total_energy,
                max_energy=max_energy,
                load_factor=load_factor,
                energy_distribution=energy_distribution
            )
            
            return Response({
                'file_id': file_id,
                'year': year,
                'turbine_type': turbine_type,
                'distribution_type': distribution_type,
                'total_energy': float(total_energy),
                'max_energy': float(max_energy),
                'load_factor': float(load_factor),
                'energy_distribution': energy_distribution
            })
            
        except (WindDataFile.DoesNotExist, WindAnalysis.DoesNotExist, DistributionAnalysis.DoesNotExist):
            return Response(
                {'error': 'File, analysis, or distribution not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error calculating energy potential: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
class WindDataFileListView(ListAPIView):
    queryset = WindDataFile.objects.all()
    serializer_class = WindDataFileSerializer

class WindDataFileDetailView(RetrieveAPIView):
    queryset = WindDataFile.objects.all()
    serializer_class = WindDataFileSerializer