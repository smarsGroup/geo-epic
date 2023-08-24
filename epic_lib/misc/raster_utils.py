import numpy as np
import pandas as pd
import rasterio
from osgeo import gdal, osr
from pyproj import Transformer
from sklearn.neighbors import BallTree

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