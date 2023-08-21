import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.neighbors import BallTree
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import rasterio
from osgeo import gdal, osr
from pyproj import Transformer


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



def raster_to_dataframe(raster_file):
    """
    Converts .tiff file to DataFrame with pixel locations and band values.
    """
    with rasterio.open(raster_file) as src:
        bands = src.read() 
        trans = src.transform
        band_names = src.descriptions

    # Get the location of pixel centers
    lon_coords, lat_coords = _lon_lat_coords(trans, bands[0].shape)

    # Create a dictionary with coordinates and band data
    data_dict = {'x': lon_coords, 'y': lat_coords}
    for i, band in enumerate(bands, 1):
        band_name = band_names[i-1] if band_names[i-1] else f'band_{i}'
        data_dict[band_name] = band.flatten()

    return pd.DataFrame(data_dict)


def sample_raster_nearest(raster_file, coords, crs = "EPSG:4326"):
    """
    Sample a raster file at specific coordinates, taking the nearest pixel.
    raster_file: path to the raster file
    coords: a list of (x, y)/(lat, lon) tuples
    crs: the crs the coords are in.
    return: a dictionary with band names as keys and lists of pixel values at the given coordinates as values
    """
    with rasterio.open(raster_file) as src:
        bands = src.read() 
        band_names = src.descriptions
        # Convert coordinates to raster's CRS
        transformer = Transformer.from_crs(crs, src.crs, always_xy = True)
        transformed_coords = np.array([transformer.transform(*coord) for coord in coords])
        # Get the values of the nearest pixels
        rows, cols = src.index(*transformed_coords.T)
        samples = {"x": transformed_coords[:, 0], "y": transformed_coords[:, 1]}
        for i, band in enumerate(bands, 1):
            band_name = band_names[i-1] if band_names[i-1] else f'band_{i}'
            samples[band_name] = band[rows, cols]
    return pd.DataFrame(samples)

class LatLonLookup:
    def __init__(self, raster_file):
        df = raster_to_dataframe(raster_file)
        self.tree = BallTree(df[['x', 'y']].values)
        self.ids = df['band_1'].values
        
    def get(self, lat, lon):
        _, index = self.tree.query([[lat, lon]], k = 1)
        nearest_index = index[0][0]
        return self.ids[nearest_index]

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

def reproject_crop_raster(src, dst, out_epsg, min_coords, max_coords):
    """
    Reproject and crop a raster file.
    src_filename: Source file path.
    dst_filename: Destination file path.
    out_epsg: Output coordinate system as EPSG code.
    min_lon, min_lat, max_lon, max_lat: Bounding box coordinates.
    """
    # Define target SRS
    out_srs = osr.SpatialReference()
    out_srs.ImportFromEPSG(out_epsg)
    
    # Call Warp function
    gdal.Warp(dst, src, format='GTiff', 
              outputBounds = [*min_coords, *max_coords], 
              dstSRS = out_srs)
    
    
def _lon_lat_coords(trans, shape):
    """
    Computes longitude, latitude coordinates for pixel centers.
    """
    # Create a new Affine object with modified c and f attributes
    t_shifted = rasterio.Affine(trans.a, trans.b, trans.c + trans.a/2, 
                                trans.d, trans.e, trans.f + trans.e/2)
    indices = np.indices(shape)
    lon_coords, lat_coords = t_shifted * (indices[1].flatten(), indices[0].flatten())
    return lon_coords, lat_coords


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

