import numpy as np
from scipy.optimize import least_squares
from scipy import signal
from scipy.stats import norm

class AsymmetricGaussian:
    def __init__(self):
        # Parameters: amplitude, center, sigma, alpha (skewness)
        self.params = 1.0, 180, 30, 0

    def asymmetric_gaussian(self, x, amplitude, center, sigma, alpha):
        """Asymmetric Gaussian function equation."""
        z = (x - center) / sigma
        return amplitude * norm.pdf(z) * norm.cdf(alpha * z)

    def derivative(self, x, n=1):
        """Calculate the n-th derivative of the asymmetric Gaussian at point x."""
        amplitude, center, sigma, alpha = self.params
        z = (x - center) / sigma

        if n == 1:
            return amplitude * (norm.pdf(z) * norm.cdf(alpha * z) * (-z / sigma) +
                                norm.pdf(z) * norm.pdf(alpha * z) * (alpha / sigma))
        elif n == 2:
            return amplitude * (norm.pdf(z) * norm.cdf(alpha * z) * (z**2 - 1) / sigma**2 +
                                norm.pdf(z) * norm.pdf(alpha * z) * (-2 * alpha * z) / sigma**2 +
                                norm.pdf(z) * norm.cdf(alpha * z) * (-alpha**2 * z) / sigma**2)
        elif n == 3:
            return amplitude * (norm.pdf(z) * norm.cdf(alpha * z) * (-z**3 + 3*z) / sigma**3 +
                                norm.pdf(z) * norm.pdf(alpha * z) * (3 * alpha * z**2 - alpha) / sigma**3 +
                                norm.pdf(z) * norm.cdf(alpha * z) * (alpha**2 * z**2 - alpha**2) / sigma**3)
        else:
            raise ValueError("Derivative order n must be 1, 2, or 3.")

    def fit(self, xdata, ydata):
        """Fit the asymmetric Gaussian model to the data."""
        loss = lambda args: self.asymmetric_gaussian(xdata, *args) - ydata
        popt = least_squares(loss, self.params, loss='cauchy', f_scale=0.5, max_nfev=100000,
                             bounds=([0, 0, 0, -5], [10, 365, 100, 5]))
        self.params = popt.x

    def __call__(self, x):
        """Predict y values using the fitted model."""
        return self.asymmetric_gaussian(x, *self.params)

    def get_dates(self):
        """Calculate phenological days of year (DOYs)"""
        doy = np.arange(365)
        diff2 = self.derivative(doy, 2)
        peaks, _ = signal.find_peaks(diff2)
        valleys, _ = signal.find_peaks(-diff2)

        if len(peaks) > 0 and len(valleys) > 0:
            emergence = peaks[0]
            harvest = valleys[-1]
        else:
            # Fallback method if peaks/valleys are not found
            amplitude, center, sigma, _ = self.params
            emergence = max(0, int(center - sigma))
            harvest = min(364, int(center + sigma))

        return emergence, harvest