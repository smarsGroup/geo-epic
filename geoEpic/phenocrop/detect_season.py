import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import math

def calc_num_seasons_single(df, index_col):
    """
    Calculate the number of seasons (significant peaks) for a single time series.

    Parameters
    ----------
    df : pandas DataFrame
        A DataFrame with a 'date' column in 'yyyy-mm-dd' format and one vegetation index column.
    index_col : str
        The name of the column containing the vegetation index (e.g., 'ndvi').

    Returns
    -------
    num_seasons : int
        The number of significant peaks detected in the time series.
    """
    # Ensure 'date' column is in datetime format
    df['date'] = pd.to_datetime(df['date'])
    
    # Sort by date
    df = df.sort_values('date')
    
    # Remove NaN values
    vec_data = df[index_col].dropna()
    
    # Get height (75% threshold) and distance (4 seasons assumption)
    if len(vec_data) == 0:
        return 0
    height = np.nanquantile(vec_data, q=0.75)
    distance = math.ceil(len(vec_data) / 4)
    
    # Find peaks
    peaks, _ = find_peaks(vec_data, height=height, distance=distance)
    
    # Return the number of peaks
    return len(peaks)

