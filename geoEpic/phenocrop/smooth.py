import pandas as pd
import numpy as np
from scipy.signal import savgol_filter, gaussian_filter1d

def smooth_df(df, method='savitsky', window_length=3, polyorder=1, sigma=1, index_col=None):
    """
    Smooths a time series in a pandas DataFrame using the specified method.

    Parameters
    ----------
    df : pandas DataFrame
        A DataFrame with a 'date' column in 'yyyy-mm-dd' format and at least 
        one column containing the index to smooth (e.g., 'ndvi').
    method : str
        The smoothing algorithm to apply. Options are:
        - 'savitsky': Savitzky-Golay smoothing.
        - 'symm_gaussian': Symmetrical Gaussian smoothing.
    window_length : int
        The length of the filter window (positive odd integer). Larger values result in more smoothing.
        Used for the Savitzky-Golay method.
    polyorder : int
        The order of the polynomial used to fit the samples. Must be less than window_length.
        Used for the Savitzky-Golay method.
    sigma : int
        Standard deviation for Gaussian kernel. Must be between 1-9. Used for the Gaussian method.
    index_col : str
        The column to smooth in the DataFrame (e.g., 'ndvi').

    Returns
    -------
    smoothed_df : pandas DataFrame
        A copy of the input DataFrame with an additional column, '<index_col>_smoothed',
        containing the smoothed time series.
    """
    
    # Notify user
    print(f'Smoothing method: {method} with window length: {window_length} and polyorder: {polyorder}.')
    
    # Validate input
    if 'date' not in df.columns:
        raise ValueError('> "date" column not found. Ensure the DataFrame has a "date" column in yyyy-mm-dd format.')
    if index_col not in df.columns:
        raise ValueError(f'> "{index_col}" column not found. Ensure the DataFrame contains the specified column to smooth.')
    
    # Ensure 'date' column is in datetime format
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')  # Sort by date
    
    # Extract the series to smooth
    series = df[index_col].dropna()
    
    if len(series) < window_length:
        raise ValueError(f"> The series is too short for the specified window_length={window_length}.")
    
    # Perform smoothing
    if method == 'savitsky':
        if window_length % 2 == 0 or window_length <= 0:
            raise ValueError('> Window_length must be a positive odd integer.')
        if polyorder >= window_length:
            raise ValueError('> Polyorder must be less than window_length.')
        
        smoothed_values = savgol_filter(series, window_length=window_length, polyorder=polyorder)
    
    elif method == 'symm_gaussian':
        if not (1 <= sigma <= 9):
            raise ValueError('> Sigma must be between 1 and 9.')
        
        smoothed_values = gaussian_filter1d(series, sigma=sigma)
    
    else:
        raise ValueError('> Provided method not supported. Please use "savitsky" or "symm_gaussian".')
    
    # Add smoothed values back to DataFrame
    smoothed_series = pd.Series(smoothed_values, index=series.index)
    smoothed_col_name = f'{index_col}_smoothed'
    df[smoothed_col_name] = smoothed_series
    
    # Notify user
    print('> Smoothing successful.\n')
    
    return df
