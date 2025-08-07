import numpy as np
from scipy.interpolate import interp1d

class TurbineCalculator:
    # Predefined turbine power curves
    TURBINES = {
        'bergey_excel_10': {
            'power_curve': np.array([
                [0, 0], [1, 0], [2, 0], [3, 0.1], [4, 0.4], [5, 0.85], 
                [6, 1.51], [7, 2.4], [8, 3.6], [9, 5.07], [10, 6.86], 
                [11, 8.86], [12, 10.89], [13, 12.02], [14, 12.4], 
                [15, 12.4], [16, 12.4]
            ]),
            'rated_power': 8.86  # kW
        },
        'bergey_excel_15': {
            'power_curve': np.array([
                [0, 0], [1, 0], [2, 0], [3, 0.11], [4, 0.68], [5, 2.07], 
                [6, 3.82], [7, 6.09], [8, 8.5], [9, 11.27], [10, 13.66], 
                [11, 15.61], [12, 16.88], [13, 18.21], [14, 19.1], 
                [15, 20.25], [16, 20.25], [17, 20.25]
            ]),
            'rated_power': 15.61  # kW
        },
        'cf_20': {
            'power_curve': np.array([
                [0, 0], [1, 0], [2, 0], [3, 0], [4, 0.70], [5, 2.07], 
                [6, 3.92], [7, 6.72], [8, 10.59], [9, 14.89], [10, 18.94], 
                [11, 20.08], [12, 20.08], [13, 20.08], [14, 20.08], 
                [15, 20.08], [16, 20.08], [17, 20.08], [18, 20.08]
            ]),
            'rated_power': 20.08  # kW
        }
    }
    
    def __init__(self, probabilities, bin_edges):
        """
        Initialize with wind speed probabilities and bin edges
        
        Args:
            probabilities: List of probabilities for each wind speed bin
            bin_edges: List of bin edges (e.g., [0, 1, 2, ...])
        """
        self.probabilities = probabilities
        self.bin_edges = bin_edges
        self.bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    def calculate_for_all_turbines(self):
        """Calculate energy production for all turbine types"""
        results = {}
        for turbine_name, turbine_data in self.TURBINES.items():
            results[turbine_name] = self._calculate_for_turbine(
                turbine_data['power_curve'],
                turbine_data['rated_power']
            )
        return results
    
    def _calculate_for_turbine(self, power_curve, rated_power):
        """
        Calculate energy production for a specific turbine
        
        Args:
            power_curve: Numpy array with [wind_speed, power_output] pairs
            rated_power: Rated power of the turbine in kW
            
        Returns:
            Dictionary with calculation results
        """
        # Create interpolation function for power curve
        power_interp = interp1d(
            power_curve[:, 0], 
            power_curve[:, 1], 
            kind='linear', 
            fill_value='extrapolate'
        )
        
        # Calculate power output for each bin center
        power_outputs = power_interp(self.bin_centers)
        
        # Calculate hours per year for each bin
        hours_per_year = 8760  # Total hours in a year
        hours_in_bins = np.array(self.probabilities) * hours_per_year
        
        # Calculate energy per bin (kWh)
        energy_per_bin = hours_in_bins * power_outputs
        
        # Calculate total energy (kWh)
        total_energy = np.sum(energy_per_bin)
        
        # Calculate maximum possible energy (kWh)
        max_energy = rated_power * hours_per_year
        
        # Calculate load factor (%)
        load_factor = (total_energy / max_energy) * 100 if max_energy > 0 else 0
        
        # Prepare energy distribution by bin
        energy_distribution = [
            {
                'bin_start': float(self.bin_edges[i]),
                'bin_end': float(self.bin_edges[i+1]),
                'energy': float(energy_per_bin[i])
            }
            for i in range(len(energy_per_bin))
        ]
        
        return {
            'total_energy': float(total_energy),
            'max_energy': float(max_energy),
            'load_factor': float(load_factor),
            'energy_distribution': energy_distribution,
            'rated_power': float(rated_power)
        }