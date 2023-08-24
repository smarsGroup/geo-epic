import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.neighbors import BallTree
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed


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


def writeDATFiles(new_dir, base_dir, fid, row):
    with open(f'{new_dir}/EPICRUN.DAT', 'w') as ofile:
        fmt = '%8d %8d %8d 0 1 %8d  %8d  %8d  0   0  25   1995   10.00   2.50  2.50  0.1/'
        np.savetxt(ofile, [[int(fid)]*6], fmt=fmt)
        
    with open(f'{new_dir}/ieSite.DAT', 'w') as ofile:
        site_src = base_dir + '/site'
        fmt = '%8d    "%s/%d.sit"\n'%(fid, site_src, fid)
        ofile.write(fmt)

    with open(f'{new_dir}/ieSllist.DAT', 'w') as ofile:
        soil_src = base_dir + '/soil/files'
        fmt = '%8d    "%s/%d.SOL"\n'%(fid, soil_src, row['ssu'])  
        ofile.write(fmt)

    with open(f'{new_dir}/ieWedlst.DAT', 'w') as ofile:
        fmt = '%8d    "%d.DLY"\n'%(fid, fid)  
        ofile.write(fmt)

    with open(f'{new_dir}/ieWealst.DAT', 'w') as ofile:
        fmt = '%8d    "%d.INP"   %.2f   %.2f  NB            XXXX\n'%(fid, fid, row['x'], row['y'])
        ofile.write(fmt)
    
    with open(f'{new_dir}/ieOplist.DAT', 'w') as ofile:
        opc_src = base_dir + '/opc'
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


def parallel_executor(func, args, method = 'Process', max_workers = 20, return_value = False, bar = True):
    """
    Executes a function across multiple processes and collects the results.

    Args:
        func: The function to execute.
        method: string as Process or Thread.
        args: An iterable of arguments to pass to the function.
        max_workers: The maximum number of processes to use.
        return_value: A boolean indicating whether the function returns a value.

    Returns:
        results: If return_value is True, a list of results from the function executions sorted according to 
                 If return_value is False, an empty list is returned.
        failed_indices: A list of indices of arguments for which the function execution failed.
    """
    failed_indices = []
    results = [None] * len(args) if return_value else []
    PoolExecutor = {'Process': ProcessPoolExecutor, 'Thread':  ThreadPoolExecutor}[method]
    with PoolExecutor(max_workers = max_workers) as executor:
        if bar: pbar = tqdm(total = len(args))
        futures = {executor.submit(func, arg): i for i, arg in enumerate(args)}
        try:
            for future in as_completed(futures):
                ind = futures[future]
                if future.exception() is not None:
                    print(f'\nFunction execution failed for args:\n {args[ind]}')
                    print(f'Exception: {future.exception()}.\n')
                    failed_indices.append(ind)
                elif return_value:
                        results[ind] = future.result()
                if bar: pbar.update(1)
        except:
            return results, failed_indices
        if bar: pbar.close()
    return results, failed_indices

