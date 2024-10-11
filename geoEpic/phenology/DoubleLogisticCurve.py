from scipy.optimize import least_squares
from scipy.special import expit
from scipy import signal
import numpy as np


class DoubleLogisticCurve:
    def __init__(self):
        # Parameters for the first and second logistic curves
        self.params = 5.5, 0.12, 150, 0.12, 250  
    
    def double_logistic(self, x, c, k1, x0_1, k2, x0_2):
        """Double logistic curve equation, representing the sum of two logistic curves."""
        return c * (expit(k1 * (x - x0_1)) - expit(k2 * (x - x0_2)))

    def derivative(self, x, n=1):
        """Calculate the n-th derivative of the double logistic curve at point x."""
        c, k1, x0_1, k2, x0_2 = self.params
        if n == 1:
            return 1e2 * (c * (k1 * np.exp(-k1 * (x - x0_1)) / (1 + np.exp(-k1 * (x - x0_1)))**2 
                                - k2 * np.exp(-k2 * (x - x0_2)) / (1 + np.exp(-k2 * (x - x0_2)))**2))
        elif n == 2:
            return 1e4 * (c * k1**2 * (1 - np.exp(k1 * (x - x0_1))) * np.exp(k1 * (x - x0_1)) / (np.exp(k1 * (x - x0_1)) + 1)**3 -
                          c * k2**2 * (1 - np.exp(k2 * (x - x0_2))) * np.exp(k2 * (x - x0_2)) / (np.exp(k2 * (x - x0_2)) + 1)**3)
        elif n == 3:
            return 1e6 * (c * k1**3 * ((np.exp(k1 * (x - x0_1)) + 1)**2 - 6 * np.exp(k1 * (x - x0_1))) * np.exp(k1 * (x - x0_1)) / (np.exp(k1 * (x - x0_1)) + 1)**4 -
                          c * k2**3 * ((np.exp(k2 * (x - x0_2)) + 1)**2 - 6 * np.exp(k2 * (x - x0_2))) * np.exp(k2 * (x - x0_2)) / (np.exp(k2 * (x - x0_2)) + 1)**4)
        else:
            raise ValueError("Derivative order n must be 1, 2, or 3.")
    
    def fit(self, xdata, ydata):
        """Fit the double logistic model to the data."""
        def residuals(args):
            # Compute the residuals
            res = self.double_logistic(xdata, *args) - ydata
            # Penalize underestimations more than overestimations
            res[res < 0] *= 10  # Adjust the factor as needed
            return res
        
        # Perform least squares optimization with the custom residuals
        popt = least_squares(
            residuals,
            self.params,
            loss='linear',  # Use linear loss for custom residuals
            max_nfev=100000,
            bounds=([3, 0.01, 0, 0.01, 50], [8.5, 0.12, 250, 0.15, 365])
        )
        self.params = popt.x

    def __call__(self, x):
        """Predict y values using the fitted model."""
        return self.double_logistic(x, *self.params)
    
    def get_dates(self):
        """Calculate Phenological doys"""
        doy = np.arange(365)
        diff3 = self.derivative(doy, 3)
        peaks, _ = signal.find_peaks(diff3, height = 0)
        # print()
        emergence = peaks[0]
        peaks, _ = signal.find_peaks(-diff3, height = 0)
        harvest = peaks[-1]

        return emergence, harvest
    

class HarmonicCurve:
    def __init__(self):
        # Initialize parameters for the harmonic function (c1 to c9)
        self.params = np.ones(9)
    
    def harmonic(self, x, c1, c2, c3, c4, c5, c6, c7, c8, c9):
        """Harmonic function with up to third-order harmonics."""
        w = 2 * np.pi / 365  # Fundamental frequency for annual data
        return (c1 + c2 * x + c3 * x**2 +
                c4 * np.sin(w * x) + c5 * np.cos(w * x) +
                c6 * np.sin(2 * w * x) + c7 * np.cos(2 * w * x) +
                c8 * np.sin(3 * w * x) + c9 * np.cos(3 * w * x))
    
    def fit(self, xdata, ydata):
        """Fit the harmonic model to the data."""
        def residuals(args):
            return self.harmonic(xdata, *args) - ydata
        
        # Initial parameter estimates
        initial_params = self.params
        
        # Perform least squares optimization
        result = least_squares(
            residuals,
            initial_params,
            loss='cauchy',    # Robust to outliers
            f_scale=0.5,
            max_nfev=100000,
            bounds=(-np.inf, np.inf)
        )
        self.params = result.x
    
    def __call__(self, x):
        """Predict y values using the fitted model."""
        return self.harmonic(x, *self.params)
    
    def find_seasons(self, xdata):
        """Determine the number of seasons and their durations."""
        # Predict y values using the fitted model
        y_fitted = self.__call__(xdata)
        
        # Find peaks (local maxima) in the fitted curve
        peaks, _ = signal.find_peaks(y_fitted)
        
        # Positions of the peaks (days of the year)
        peak_positions = xdata[peaks]
        
        # Calculate durations between peaks
        durations = np.diff(peak_positions)
        
        # Number of seasons is the number of peaks
        number_of_seasons = len(peaks)
        
        return number_of_seasons, peak_positions, durations
    
