import pandas as pd
import geopandas as gpd

def create_run_info(shpfile,run_info_loc):
    """
    Process a GeoDataFrame to ensure it contains 'CSBID' and 'SiteID' and create 'SiteID' if missing.
    
    Parameters:
    shpfile (str): The path to the shapefile.
    
    Returns:
    GeoDataFrame: The processed GeoDataFrame with 'CSBID', 'SiteID', 'lon', and 'lat' columns.
    
    Raises:
    ValueError: If 'CSBID' and 'SiteID' are both missing.
    """
    # Read the shapefile into a GeoDataFrame
    gdf = gpd.read_file(shpfile)
    
    # Check if 'CSBID' and 'SiteID' columns are present
    
    if 'SiteID' not in gdf.columns:
        if 'CSBID' not in gdf.columns:
            raise ValueError("'CSBID' is missing in the shapefile.")
        # If 'SiteID' is missing, create 'SiteID' from 'CSBID' by removing the first 6 characters and converting to int
        prefix = str(gdf['CSBID'].iloc[0])[:6]
        all_same_prefix = gdf['CSBID'].astype(str).str.startswith(prefix).all()

        if all_same_prefix:
            # Remove the first 6 characters of 'CSBID' and convert to integer
            gdf['SiteID'] = gdf['CSBID'].astype(str).str[6:].astype(int)
        else:
            raise ValueError("Not all 'CSBID' values have the same prefix. Cannot generate 'SiteID'.")
    
    # Compute centroids and extract longitude and latitude
    gdf['lon'] = gdf.geometry.centroid.x
    gdf['lat'] = gdf.geometry.centroid.y
    
    gdf[['SiteID', 'lat', 'lon']].to_csv(run_info_loc,index=False)