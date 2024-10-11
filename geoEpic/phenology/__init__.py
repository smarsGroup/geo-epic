#this file contains, utils for 
# interpolation
# savitzky-golay filter
# adaptive savitzky-golay filter

import numpy as np
from scipy.interpolate import interp1d
from scipy.ndimage import gaussian_filter
from scipy.signal import savgol_filter

def interpolate_data(x, y, x_new):
    """
    Interpolate data using a cubic spline interpolation.

    Args:
        x (array-like): The x-values of the data points.
        y (array-like): The y-values of the data points.
        x_new (array-like): The new x-values for interpolation.

    Returns:
        array-like: The interpolated y-values.
    """
    f = interp1d(x, y, kind='cubic')
    return f(x_new)

def adaptive_savgol_filter(y, window_size, order, deriv=0, rate=1):
    