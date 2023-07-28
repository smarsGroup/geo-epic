import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.neighbors import BallTree
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

def read_dly(path):
    """
    Reads a DLY file into DataFrame.
    """
    data = pd.read_fwf(f'{path}.DLY', widths=[6, 4, 4, 6, 6, 6, 6, 6, 6], header=None)
    data.columns = ['year', 'month', 'day', 'srad', 'tmax', 'tmin', 'prcp', 'rh', 'ws']
    return data
 

def write_dly(path, data):
    """
    Writes DataFrame into a DLY file.
    """
    with open(f'{path}.DLY', 'w') as ofile:
        fmt = '%6d%4d%4d%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f'
        np.savetxt(ofile, data.values[1:], fmt=fmt)


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


def create_epicfiles(df, path):
    """
    Assumes the data frame have required columns
    """
    with open(f'{path}/EPICRUN.DAT', 'w') as ofile:
        fmt = '%8d %8d %8d 0 1 %8d %8d %8d 0 /'
        np.savetxt(ofile, df[['ID']*6].values, fmt=fmt)

    with open(f'{path}/ieSite.DAT', 'w') as ofile:
        fmt = '%8d    "../../common_inputfiles/soils/%s.sit"'
        np.savetxt(ofile, df[['ID', 'site']].values, fmt=fmt)

    with open(f'{path}/ieSllist.DAT', 'w') as ofile:
        fmt = '%8d    "../../common_inputfiles/soils/%s.SOL"'  
        np.savetxt(ofile, df[['ID', 'soil']].values, fmt=fmt)
    
    with open(f'{path}/ieOpList.DAT', 'w') as ofile:
        fmt = '%8d    "../../common_inputfiles/OPC/%s.OPC"'  
        np.savetxt(ofile, df[['ID', 'ID']].values, fmt=fmt)
    
    with open(f'{path}/ieWedlst.DAT', 'w') as ofile:
        fmt = '%8d    "../../common_inputfiles/daily/%s.DLY"'  
        np.savetxt(ofile, df[['ID', 'dly']].values, fmt=fmt)
    
    with open(f'{path}/ieWealst.DAT', 'w') as ofile:
        fmt = '%8d    "../../common_inputfiles/monthly/%s.INP"   %.2f   %.2f  NB            XXXX'  
        np.savetxt(ofile, df[['ID', 'dly', 'x', 'y']].values, fmt=fmt)


def parallel_executor(func, args, method = 'Process', max_workers = 20, return_value = False):
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
        pbar = tqdm(total = len(args))
        futures = {executor.submit(func, arg): i for i, arg in enumerate(args)}
        try:
            for future in as_completed(futures):
                ind = futures[future]
                if future.exception() is not None:
                    print(f'Function execution failed for args:\n {args[ind]}')
                    print(f'Exception: {future.exception()}.')
                    failed_indices.append(ind)
                elif return_value:
                        results[ind] = future.result()
                pbar.update(1)
        except:
            return results, failed_indices
        pbar.close()
    return results, failed_indices

