import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from geoEpic.io import ACY,DGN,DataLogger
from geoEpic.utils import parallel_executor

data_logger = DataLogger(os.path.join(f".cache"))
# crop_dict = {}

def remove_outliers_and_interpolate(df, var, method='median', user_factor=2, z_pval=0.05):
    """
    Removes outliers in the NDVI column of a DataFrame and interpolates missing values.

    Args:
        df (pd.DataFrame): DataFrame with 'Date' and 'NDVI' columns.
        method (str): Outlier detection method ('median' or 'zscore').
        user_factor (float): Multiplier for the cutoff threshold (applies to 'median' method).
        z_pval (float): P-value for z-score method (default 0.05).

    Returns:
        pd.DataFrame: DataFrame with outliers removed and interpolated.
    """
    # Ensure the input DataFrame has the required columns
    if 'Date' not in df.columns or var not in df.columns:
        raise ValueError(f"DataFrame must contain 'Date' and {var} columns.")
    
    # Ensure 'Date' is a datetime object
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)

    # Generate a full date range and reindex the DataFrame
    full_date_range = pd.date_range(start=df['Date'].min(), end=df['Date'].max(), freq='D')
    df = df.set_index('Date').reindex(full_date_range).rename_axis('Date').reset_index()

    # Calculate the cutoff or critical values for outlier detection
    if method == 'median':
        # Rolling median approach
        window_size = int(len(df) / 7) if len(df) > 21 else 3
        window_size = max(3, window_size if window_size % 2 != 0 else window_size + 1)
        
        # Calculate rolling median
        rolling_median = df[var].rolling(window=window_size, center=True).median()
        
        # Calculate cutoff values based on standard deviation and user factor
        cutoff = df[var].std() * user_factor
        
        # Identify outliers
        abs_diff = abs(df[var] - rolling_median)
        outliers = abs_diff > cutoff

    elif method == 'zscore':
        # Z-score approach
        if z_pval == 0.01:
            crit_val = 2.3263
        elif z_pval == 0.05:
            crit_val = 1.6449
        elif z_pval == 0.1:
            crit_val = 1.2816
        else:
            raise ValueError("Invalid z_pval. Use 0.1, 0.05, or 0.01.")
        
        # Calculate z-scores
        z_scores = zscore(df[var].dropna())
        outliers = abs(z_scores) > crit_val
    else:
        raise ValueError("Unsupported method. Use 'median' or 'zscore'.")

    # Replace outliers with NaN
    df.loc[outliers, var] = np.nan

    # Interpolate missing values
    df[var] = df[var].interpolate(method='linear')

    return df

def _profile_field_with_csv(data):

    field_id = data['field_id']
    lai_output_dir =  data['lai_output_dir']
    years = data['years']
    cdl_code = data['cdl_code']
    cdl_dir = data['cdl_dir']
    var = data['var']
    is_winter_crop = data['is_winter_crop']
    
    lai_file = os.path.join(lai_output_dir,f'{field_id}.csv')
    cdl_file = os.path.join(cdl_dir,f'{field_id}.csv')

    if( not os.path.exists(lai_file) ):
        return
    
    if( not os.path.exists(cdl_file) ):
        return
    
    
    
    crop_df = pd.read_csv(cdl_file, parse_dates=['Date'])
    if 'year' not in crop_df.columns:
        crop_df['year'] = crop_df['Date'].dt.year
    
    df = pd.read_csv(lai_file, parse_dates=['Date'])
    # date_range = pd.date_range(start=df['Date'].min(), end=df['Date'].max())
    # df = df.set_index('Date').reindex(date_range).interpolate().reset_index()
    # df = df.rename(columns={'index': 'Date'})
    df['Year'] = df['Date'].dt.year
    # print(df)
    
    for year in years:
        try:
            crop_code = crop_df.loc[(crop_df['year'] == year),'cdl_code']
            crop_code = int(crop_code.iloc[0])
            if( crop_code!=cdl_code ):
                continue
            # print(f'{crop_code} : {field_id} : {year}')
            if is_winter_crop:
                previous_year = year - 1
                df_filtered = df[
                    ((df['Date'].dt.year == previous_year) & (df['Date'].dt.month >= 9)) |  # Sep-Dec of previous year
                    ((df['Date'].dt.year == year) & (df['Date'].dt.month <= 7))            # Jan-Jul of current year
                ].copy()
            else:
                df_filtered = df[df['Date'].dt.year == year].copy()
                
            df_filtered = df_filtered[df_filtered[var] > 0]
            
            # df_filtered = df_filtered[df_filtered['LAI'] > 0]
            df_filtered.loc[:, 'Month_Day'] = df_filtered['Date'].dt.strftime('%m-%d')
            
            df_filtered = df_filtered[['Month_Day',var]]
            # print(df_filtered)
            for index, row in df_filtered.iterrows():
                row_dict = row.to_dict()
                if( row_dict[var]==0):
                    continue
                filtered_dict = {k: v for k, v in row_dict.items() if v != 0}
                data_logger.log_dict(f'csv_{cdl_code}_{var}', filtered_dict)
        except Exception as e:
            print(e)
            
def _profile_field_epic_output(data):
    # print(data)
    field_id = data['field_id']
    epic_output_dir =  data['epic_output_dir']
    years = data['years']
    cdl_code = data['cdl_code']
    cdl_dir = data['cdl_dir']
    var = data['var']
    is_winter_crop = data['is_winter_crop']
    
    cdl_file = os.path.join(cdl_dir,f'{field_id}.csv')
    dgn_file = os.path.join(epic_output_dir,f'{field_id}.DGN')
    
    if( not os.path.exists(dgn_file) ):
        return
    
    if( not os.path.exists(cdl_file) ):
        return
    
    dgn = DGN(dgn_file)
    
    crop_df = pd.read_csv(cdl_file, parse_dates=['Date'])
    if 'year' not in crop_df.columns:
        crop_df['year'] = crop_df['Date'].dt.year
    
    var_df = dgn.get_var(var)
    for year in years:
        # try:
        crop_code = crop_df.loc[(crop_df['year'] == year),'cdl_code']
        crop_code = int(crop_code.iloc[0])
        if( crop_code!=cdl_code ):
            continue
        
        if is_winter_crop:
            previous_year = year - 1
            df_filtered = var_df[
                ((var_df['Date'].dt.year == previous_year) & (var_df['Date'].dt.month >= 9)) |  # Sep-Dec of previous year
                ((var_df['Date'].dt.year == year) & (var_df['Date'].dt.month <= 7))            # Jan-Jul of current year
            ]
        else:
            df_filtered = var_df[var_df['Date'].dt.year == year]

        df_filtered = df_filtered[df_filtered['LAI'] > 0]
        
        if not df_filtered.empty:            

            df_filtered['Month_Day'] = df_filtered['Date'].dt.strftime('%m-%d') 

            df_filtered = df_filtered[['Month_Day',var]]
            
            # print(df_filtered)
            for index, row in df_filtered.iterrows():
                row_dict = row.to_dict()
                filtered_dict = {k: v for k, v in row_dict.items() if v != 0}
                data_logger.log_dict(f'{cdl_code}_{var}', filtered_dict)
        # crop_dict[crop_name] = crop_dict.get(crop_name,0)+1

        # except Exception as e:
        #     print(e)
        #     continue

def process_ndvi_data(combined_data,var):
    
    # Initialize a dictionary to store results
    result = {'Month_Day': [], f'Min_{var}': [], f'Max_{var}': [], f'Mean_{var}': []}
    
    # Group by 'Month_Day' to calculate percentiles for each day
    grouped = combined_data.groupby('Month_Day')[var]
    
    
    for month_day, values in grouped:
        # print(f'{month_day} : {values}')
        min_val = np.percentile(values, 10)
        max_val = np.percentile(values, 90)
        mean_val = values.mean()  # Calculate the mean
        
        result['Month_Day'].append(month_day)
        result[f'Min_{var}'].append(min_val)
        result[f'Max_{var}'].append(max_val)
        result[f'Mean_{var}'].append(mean_val)
    
    # Convert result to a DataFrame
    result_df = pd.DataFrame(result)
    
    return result_df

def profile_lai_from_output( years, epic_output_dir, cdl_dir, cdl_code, output_dir, output_name, is_winter_crop=False):
    
    var = 'LAI'
    existing_field_ids = set([f.split('.')[0] for f in os.listdir(epic_output_dir)])
    existing_field_ids = list(existing_field_ids)
    
    list_of_fields = [{'field_id': field_id, 'years': years, 'epic_output_dir': epic_output_dir, 'cdl_code':cdl_code, 'cdl_dir':cdl_dir, 'var':'LAI', 'is_winter_crop':is_winter_crop} for field_id in existing_field_ids]

    # for i in range(100):
    #     print(list_of_fields[i])
    #     _profile_field(list_of_fields[i])
    parallel_executor(_profile_field_epic_output, list_of_fields, max_workers = 55, return_value = False)
    
    # txt_file = os.path.join(output_dir,'output_crop_count.txt')
    # with open(txt_file, 'a') as f:
    #     dict_str = ", ".join(f"{crop}: {value}" for crop, value in crop_dict.items()) 
    #     f.write(dict_str)

    pic_file = os.path.join(output_dir,f'{output_name}.png')
    
    combined_data = data_logger.get(f'{cdl_code}_{var}')
    if( combined_data.empty ):
        return
    dist_df = process_ndvi_data(combined_data,var)

    csv_file = os.path.join(output_dir,f'{output_name}.csv')
    dist_df.to_csv(csv_file,index=False)

    
    plt.figure(figsize=(12, 6))

    if is_winter_crop:
        dist_df['Month'] = dist_df['Month_Day'].str[:2].astype(int)
        dist_df['Year'] = dist_df['Month'].apply(lambda x: 1999 if x >= 8 else 2000)
        dist_df['Date'] = pd.to_datetime(dist_df['Year'].astype(str) + '-' + dist_df['Month_Day'], format='%Y-%m-%d')

        # Split the data into two periods
        period1 = dist_df[dist_df['Year'] == 1999]  # Aug to Dec 1999
        period2 = dist_df[dist_df['Year'] == 2000]  # Jan to Jul 2000

        plt.figure(figsize=(12, 6))

        # Plot the first period
        plt.plot(period1['Date'], period1[f'Min_{var}'], label=f'5th Percentile (Min {var})', color='blue')
        plt.plot(period1['Date'], period1[f'Max_{var}'], label=f'95th Percentile (Max {var})', color='red')
        plt.plot(period1['Date'], period1[f'Mean_{var}'], label=f'Mean (Middle) ', color='green', linestyle='--')

        # Plot the second period
        plt.plot(period2['Date'], period2[f'Min_{var}'], color='blue')
        plt.plot(period2['Date'], period2[f'Max_{var}'], color='red')
        plt.plot(period2['Date'], period2[f'Mean_{var}'], color='green', linestyle='--')
    else:
        # Create a proper datetime object
        dist_df['Date'] = pd.to_datetime('2000-' + dist_df['Month_Day'], format='%Y-%m-%d')

        # Plot the min and max NDVI values
        plt.plot(dist_df['Date'], dist_df[f'Min_{var}'], label=f'5th Percentile (Min {var})', color='blue')
        plt.plot(dist_df['Date'], dist_df[f'Max_{var}'], label=f'95th Percentile (Max {var})', color='red')
        plt.plot(dist_df['Date'], dist_df[f'Mean_{var}'], label='Mean (Middle)', color='green', linestyle='--')

    # Customize the plot
    plt.xlabel('Month-Day')
    plt.ylabel(var)
    plt.title(f'{var} Distribution (5th and 95th Percentiles) Over a Year')
    plt.legend()
    plt.xticks(rotation=90)
    plt.grid(True)

    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b'))

    # Show the plot
    plt.tight_layout()
    # plt.show()

    plt.savefig(pic_file,dpi=300, bbox_inches='tight')
    plt.close()
    
def profile_lai_from_csv(years, field_id_list, lai_output_dir, cdl_dir, cdl_code, output_dir, output_name, var, is_winter_crop=False):
    # existing_field_ids = set([f.split('.')[0] for f in os.listdir(lai_output_dir)])
    # existing_field_ids = list(existing_field_ids)
    
    list_of_fields = [{'field_id': field_id, 'years': years, 'lai_output_dir': lai_output_dir, 'cdl_code':cdl_code, 'cdl_dir':cdl_dir, 'var':var, 'is_winter_crop':is_winter_crop} for field_id in field_id_list]


    # for i in range(10):
    #     print(list_of_fields[i])
    #     _profile_field_with_csv(list_of_fields[i])
    parallel_executor(_profile_field_with_csv, list_of_fields, max_workers = 55, return_value = False)
    
    pic_file = os.path.join(output_dir,f'{output_name}.png')
    
    combined_data = data_logger.get(f'csv_{cdl_code}_{var}')
    # print(combined_data)
    if( combined_data.empty ):
        return
    dist_df = process_ndvi_data(combined_data,var)

    csv_file = os.path.join(output_dir,f'{output_name}.csv')
    dist_df.to_csv(csv_file,index=False)
    
    # if is_winter_crop:
    #     # Define the custom order for sorting
    #     custom_order = ['09', '10', '11', '12', '01', '02', '03', '04', '05', '06', '07']

    #     # Extract the month from 'Month_Day' for sorting
    #     dist_df['Month'] = dist_df['Month_Day'].str[:2]

    #     # Create a custom sort key
    #     dist_df['Sort_Order'] = dist_df['Month'].apply(lambda x: custom_order.index(x))

    #     # Sort the DataFrame by the custom order
    #     dist_df = dist_df.sort_values('Sort_Order')

    plt.figure(figsize=(12, 6))
        
    if is_winter_crop:
        dist_df['Month'] = dist_df['Month_Day'].str[:2].astype(int)
        dist_df['Year'] = dist_df['Month'].apply(lambda x: 1999 if x >= 8 else 2000)
        dist_df['Date'] = pd.to_datetime(dist_df['Year'].astype(str) + '-' + dist_df['Month_Day'], format='%Y-%m-%d')

        # Split the data into two periods
        period1 = dist_df[dist_df['Year'] == 1999]  # Aug to Dec 1999
        period2 = dist_df[dist_df['Year'] == 2000]  # Jan to Jul 2000

        plt.figure(figsize=(12, 6))

        # Plot the first period
        plt.plot(period1['Date'], period1[f'Min_{var}'], label=f'5th Percentile (Min {var})', color='blue')
        plt.plot(period1['Date'], period1[f'Max_{var}'], label=f'95th Percentile (Max {var})', color='red')
        plt.plot(period1['Date'], period1[f'Mean_{var}'], label=f'Mean (Middle) ', color='green', linestyle='--')

        # Plot the second period
        plt.plot(period2['Date'], period2[f'Min_{var}'], color='blue')
        plt.plot(period2['Date'], period2[f'Max_{var}'], color='red')
        plt.plot(period2['Date'], period2[f'Mean_{var}'], color='green', linestyle='--')
    else:
        # Create a proper datetime object
        dist_df['Date'] = pd.to_datetime('2000-' + dist_df['Month_Day'], format='%Y-%m-%d')

        # Plot the min and max NDVI values
        plt.plot(dist_df['Date'], dist_df[f'Min_{var}'], label=f'5th Percentile (Min {var})', color='blue')
        plt.plot(dist_df['Date'], dist_df[f'Max_{var}'], label=f'95th Percentile (Max {var})', color='red')
        plt.plot(dist_df['Date'], dist_df[f'Mean_{var}'], label='Mean (Middle)', color='green', linestyle='--')
        
    # Plot the min and max NDVI values
    # plt.plot(dist_df['Month_Day'], dist_df[f'Min_{var}'], label=f'5th Percentile (Min {var})', color='blue')
    # plt.plot(dist_df['Month_Day'], dist_df[f'Max_{var}'], label=f'95th Percentile (Max {var})', color='red')
    # plt.plot(dist_df['Month_Day'], dist_df[f'Mean_{var}'], label='Mean (Middle)', color='green', linestyle='--')

    # Customize the plot
    plt.xlabel('Month-Day')
    plt.ylabel(var)
    plt.title(f'{var} Distribution (5th and 95th Percentiles) Over a Year')
    plt.legend()
    plt.xticks(rotation=90)
    plt.grid(True)

    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b'))

    # Show the plot
    plt.tight_layout()
    # plt.show()

    plt.savefig(pic_file,dpi=300, bbox_inches='tight')
    plt.close()
    
def _clip_field(field):
    field_id = field["field_id"]
    cdl_path =field["cdl_dir"]
    lai_path = field["lai_dir"]
    distribution_file = field['distribution_file']
    output_path = field["output_dir"]
    cdl_code = field["cdl_code"]
    years = field["years"]
    var = field['var']
    if( not os.path.exists(os.path.join(cdl_path,f'csv/{field_id}.csv')) ):
        return
    
    if( not os.path.exists(os.path.join(lai_path,f'rs_lai/{field[1]}.csv')) ):
        return
    
    lai_df = pd.read_csv(os.path.join(lai_path,f'rs_lai/{field_id}.csv'),parse_dates=['Date'])
    lai_df['Year'] = lai_df['Date'].dt.year 

    crop_df = pd.read_csv(os.path.join(cdl_path,f'csv/{field_id}.csv'))
        
    result = None
    for year in years:
        lai_df_year =  lai_df.loc[(lai_df['Year']==year),:].copy()
        lai_df_year['Month_Day'] = pd.to_datetime(lai_df_year['Date']).dt.strftime('%m-%d')
        # print(lai_df_year)
        crop_code = crop_df.loc[(crop_df['year'] == year),'cdl_code']
        crop_code = int(crop_code.iloc[0])
        if( crop_code!=cdl_code ):
            if( result is None ):
                result = lai_df_year
            else:
                result = pd.concat([result,lai_df_year],ignore_index=True)
            continue
            
        ref_df = pd.read_csv(os.path.join(distribution_file))

        # Merge df with ref_df on month and day
        merged_df = pd.merge(lai_df_year, ref_df, on=['Month_Day'], how='left')
        
        # Check if the values are within the range and clip them if necessary
        merged_df['clipped_val'] = merged_df.apply(
            lambda row: max(row[f'Min_{var}'], min(row[var], row[f'Max_{var}'])), axis=1
        )
        merged_df = merged_df.reset_index(drop=True)
        lai_df_year.loc[:,var] = merged_df['clipped_val']
        # lai_df_year['lai_ndvi'] = np.where(11.266 * lai_df_year['ndvi'] - 4.007 < 0, 0, 11.266 * lai_df_year['ndvi'] - 4.007)
        if( result is None ):
            result = lai_df_year
        else:
            result = pd.concat([result,lai_df_year],ignore_index=True)
    result = result.drop(columns=['Month_Day','Year'])
    result.to_csv(os.path.join(output_path,f'{field_id}.csv'))
    
def clip(args):
    """
    Validates input arguments for the clip method and performs the necessary operations.
    
    Args:
        args (dict): A dictionary containing the following keys:
            - cdl_dir (str, required): Directory path for CDL data.
            - lai_dir (str, required): Directory path for LAI data.
            - years (list, required): Array of years.
            - crop_code (int, required): Integer representing the crop code.
            - distribution_file (str, required): Path to the distribution file.
            - var (any, optional): An optional variable.
    
    Raises:
        ValueError: If required fields are missing or have invalid types.
    """
    
    
    
    required_fields = {
        "cdl_dir": str,
        "lai_dir": str,
        "output_dir": str,
        "field_list" : list,
        "years": list,
        "crop_code": int,
        "distribution_file": str,
    }
    
    # Validate required fields
    for field, field_type in required_fields.items():
        if field not in args:
            raise ValueError(f"Missing required argument: '{field}'")
        if not isinstance(args[field], field_type):
            raise ValueError(f"Invalid type for '{field}'. Expected {field_type.__name__}, got {type(args[field]).__name__}")
    
    list_of_fields = [{'field_id': field_id, 'years': args.years, 'distribution_file':args["distribution_file"],'output_dir': args.output_dir, 'cdl_code':args.cdl_code, 'cdl_dir':args.cdl_dir, 'lai_dir':args.lai_dir, 'var':args.var} for field_id in args.field_list]
    
    parallel_executor(_clip_field, list_of_fields, max_workers = 55, return_value = False)
    
    
    return args


def interpolate_field(csv_path, var, start_date, end_date):
    """
    Interpolates a variable linearly for each day between start_date and end_date.

    Args:
        csv_path (str): Path to the CSV file. Must include 'date' column in 'yyyy-mm-dd' format.
        var (str): Column name of the variable to interpolate.
        start_date (str): Start date in 'yyyy-mm-dd' format.
        end_date (str): End date in 'yyyy-mm-dd' format.

    Returns:
        pd.DataFrame: DataFrame with interpolated values for the variable.
    """
    # Load the CSV file
    df = pd.read_csv(csv_path)
    
    # Ensure 'date' column exists and is in datetime format
    if 'date' not in df.columns:
        raise ValueError("The CSV file must contain a 'date' column in 'yyyy-mm-dd' format.")
    df['date'] = pd.to_datetime(df['date'])

    # Filter data to include only rows within the specified date range
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    if start_date > end_date:
        raise ValueError("start_date must be earlier than end_date.")
    
    # Generate a complete date range from start_date to end_date
    full_date_range = pd.date_range(start=start_date, end=end_date, freq='D')

    # Reindex DataFrame to include all dates in the range
    df = df.set_index('date').reindex(full_date_range).rename_axis('date').reset_index()

    # Perform linear interpolation on the specified variable
    if var not in df.columns:
        raise ValueError(f"The variable '{var}' does not exist in the CSV file.")
    df[var] = df[var].interpolate(method='linear')

    # Return the interpolated DataFrame
    return df

    