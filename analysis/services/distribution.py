from scipy.stats import norm, lognorm, weibull_min, gumbel_r
import numpy as np
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import WindDataFile, WindAnalysis, DistributionAnalysis
from scipy.stats import weibull_min

class DistributionAnalyzer:
    def __init__(self, data):
        self.data = np.array(data)
        self.data = self.data[self.data >= 0]  # Only remove negative values
        self.results = {}
    
    def analyze_all(self):
        self._analyze_normal()
        self._analyze_lognormal()
        self._analyze_weibull()
        self._analyze_gumbel()
    
    def _analyze_normal(self):
        try:
            loc, scale = norm.fit(self.data)
            self.results['normal'] = {
                'params': [loc, scale],
                'matlab_params': {
                    'mu': loc,
                    'sigma': scale
                },
                'pdf': lambda x: norm.pdf(x, loc, scale)
            }
        except Exception as e:
            print(f"Normal distribution failed: {str(e)}")
    
    def _analyze_lognormal(self):
        try:
            positive_data = self.data[self.data > 0]
            if len(positive_data) == 0:
                return
            
            # MATLAB: log(X) ~ Normal(mu, sigma)
            # SciPy: X ~ lognorm(s=sigma, scale=exp(mu), loc=0
            shape, loc, scale = lognorm.fit(positive_data, floc=0)
            mu = np.log(scale)
            sigma = shape
            
            self.results['lognormal'] = {
                'params': [shape, loc, scale],
                'matlab_params': {
                    'mu': mu,
                    'sigma': sigma
                },
                'pdf': lambda x: np.where(x > 0, lognorm.pdf(x, shape, loc, scale), 0)
            }
        except Exception as e:
            print(f"Lognormal distribution failed: {str(e)}")

    def _analyze_weibull(self):
        try:
            positive_data = self.data[self.data > 0]
            if len(positive_data) == 0:
                return
                
            # Use method='mle' to match MATLAB's approach
            params = weibull_min.fit(positive_data, floc=0, method='mle')
            c, loc, scale = params
            
            self.results['weibull'] = {
                'params': [c, loc, scale],
                'matlab_params': {
                    'a': scale,
                    'b': c
                },
                'pdf': lambda x: np.where(x > 0, weibull_min.pdf(x, c, loc, scale), 0)
            }
        except Exception as e:
            print(f"Weibull distribution failed: {str(e)}")
            
    def _analyze_gumbel(self):
        try:
            # MATLAB's gumbel fitting uses method='mm' (method of moments)
            # Calculate parameters manually to match MATLAB
            data = self.data
            beta = np.std(data) * np.sqrt(6) / np.pi  # scale parameter
            mu = np.mean(data) - 0.5772 * beta        # location parameter
            
            self.results['gumbel'] = {
                'params': [mu, beta],
                'matlab_params': {
                    'mu': mu,
                    'sigma': beta
                },
                'pdf': lambda x: gumbel_r.pdf(x, loc=mu, scale=beta),
                'cdf': lambda x: gumbel_r.cdf(x, loc=mu, scale=beta)
            }
        except Exception as e:
            print(f"Gumbel distribution failed: {str(e)}")
            self.results['gumbel'] = None