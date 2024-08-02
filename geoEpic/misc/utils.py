import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree



def find_nearest(src, dst, metric = 'minkowski', k = 1):
    """
    Find the indices in dst that correspond to each row in src based on the k nearest neighbors.
    Returns: numpy.ndarray: Indices in dst for each row in src
    """
    # Check if the metric is 'haversine' and convert DataFrame lat/lon to radians if necessary
    if metric == 'haversine':
        src = np.deg2rad(src)
        dst = np.deg2rad(dst)

    # Fit the nearest neighbors model on the destination DataFrame
    tree = BallTree(dst, metric = metric)
    _, inds = tree.query(src, k = k)
    if k == 1: inds = inds[:, 0]
    return inds


def read_gdb_layer(gdb_data, layer_name, columns = None, names = None):
    """
    Reads selected columns from a GDB layer and returns them in a pandas DataFrame.
    
    Args:
        gdb (gdb): The GDB file opened by ogr.
        layer_name (str): The name of the layer to read.
        columns (list, optional): List of column indices to read. If None, all columns are read.
        names (list, optional): List of column names corresponding to the indices in `columns`.
            If None, all column names are inferred from the layer definition.
    
    Returns:
        pd.DataFrame: The resulting dataframe.
    """
    layer = gdb_data.GetLayerByName(layer_name)
    layer_defn = layer.GetLayerDefn()

    if not columns:
        columns = list(range(layer_defn.GetFieldCount()))
        names = [layer_defn.GetFieldDefn(i).GetName() for i in columns]
    elif not names:
        names = [layer_defn.GetFieldDefn(i).GetName() for i in columns]

    features = []
    for feature in layer:
        attributes = {}
        for idx, name in zip(columns, names):
            field_defn = layer_defn.GetFieldDefn(idx)
            field_name = field_defn.GetName()
            attributes[name] = feature.GetField(field_name)
        features.append(attributes)
        
    return pd.DataFrame(features)


def writeDATFiles(new_dir, config, fid, row):
    with open(f'{new_dir}/EPICRUN.DAT', 'w') as ofile:
        fmt = '%8d %8d %8d 0 1 %8d  %8d  %8d  0   0  %2d   %4d   10.00   2.50  2.50  0.1/'
        np.savetxt(ofile, [[int(fid)]*6 + [config["duration"], config["start_year"]]], fmt=fmt)
        
    with open(f'{new_dir}/ieSite.DAT', 'w') as ofile:
        site_src = config["site"]["dir"]
        fmt = '%8d    "%s/%d.sit"\n'%(fid, site_src, fid)
        ofile.write(fmt)

    with open(f'{new_dir}/ieSllist.DAT', 'w') as ofile:
        soil_src = config["soil"]["files_dir"]
        fmt = '%8d    "%s/%d.SOL"\n'%(fid, soil_src, row['soil_id'])  
        ofile.write(fmt)
    
    daily_src = ''
    monthly_src = ''
    clim_id = fid
    
    if config['weather']['offline']:
        weather_dir = config['weather']['dir']
        daily_src = weather_dir + '/Daily/'
        monthly_src = weather_dir + '/Monthly/'
        clim_id = row['dly_id']
        

    with open(f'{new_dir}/ieWedlst.DAT', 'w') as ofile:
        fmt = '%8d    "%s%d.DLY"\n'%(fid, daily_src, clim_id)  
        ofile.write(fmt)

    with open(f'{new_dir}/ieWealst.DAT', 'w') as ofile:
        fmt = '%8d    "%s%d.INP"   %.2f   %.2f  NB            XXXX\n'%(fid, monthly_src, clim_id, row['x'], row['y'])
        ofile.write(fmt)
    
    with open(f'{new_dir}/ieOplist.DAT', 'w') as ofile:
        opc_src = config["opc_dir"]
        fmt = '%8d    "%s/%s.OPC"\n'%(fid, opc_src, row['opc'])
        ofile.write(fmt)
        
        
def calc_centroids(gdf):
    avg_lat = gdf['geometry'][0].bounds[1]
    avg_lon = gdf.total_bounds[::2].mean()
    epsg_code = 32700 if avg_lat < 0 else 32600
    epsg_code += int((avg_lon + 180) / 6) + 1
    # Calculate centroid of each polygon in UTM coordinates
    gdf = gdf.to_crs(epsg = epsg_code)
    gdf['centroid'] = gdf.centroid.to_crs(epsg=4326)
    gdf['x'] = gdf['centroid'].x
    gdf['y'] = gdf['centroid'].y
    return gdf


    
# import pandas as pd

def filter_dataframe(df, expression):
    if expression is None: return df
    if expression.count('+') < 2:
        if expression.count('+') == 1:
            exp =  [i.strip() for i in expression.split('+')]
            # print(exp)
        else:
            exp = [expression]
        # print('EXP length', len(exp))
        filtered_dfs = []
        for expression in exp:
            expressions =  [i.strip() for i in expression.split(';')]
            df_copy = df.copy()
            for expression in expressions:
                # expression = expression.strip()
                # Handle expressions that are ranges (e.g., "Range(0.35, 0.8)")
                if expression.startswith("Range(") and expression.endswith(")"):
                    values = expression[6:-1].split(',')
                    low_fraction, high_fraction = float(values[0]), float(values[1])
                    
                    # Calculate the index range
                    total_length = len(df)
                    low_idx = np.floor(low_fraction * total_length).astype(int)
                    high_idx = np.ceil(high_fraction * total_length).astype(int)
                    
                    # Ensure indices are within bounds
                    low_idx = max(0, low_idx)
                    high_idx = min(total_length, high_idx)
                    
                    df_copy = df_copy.iloc[low_idx:high_idx]

                # Handle expressions that are random (e.g., "Random(0.1)")
                elif expression.startswith("Random(") and expression.endswith(")"):
                    frac = float(expression[7:-1])
                    df_copy = df_copy.sample(frac=frac)

                # Handle boolean expressions (e.g., "group == 1")
                else:
                    df_copy = df_copy.query(expression)
            filtered_dfs.append(df_copy)

        if len(filtered_dfs) == 1:
            return filtered_dfs[0]
        else:
            filtered_df = pd.concat(filtered_dfs)
            filtered_df = filtered_df.drop_duplicates(subset = 'FieldID', keep = 'last')
            return filtered_df

            
    return df.reset_index()
    
