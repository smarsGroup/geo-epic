from flask import Flask, render_template, request
import geopandas as gpd
import folium
from folium.plugins import Draw
import json

app = Flask(__name__)

@app.route('/map')
def map():
    return render_template('map.html')

@app.route('/save', methods=['POST'])
def save():
    data = request.get_json()
    # Save the GeoJSON data to a file
    with open('data.geojson', 'w') as f:
        json.dump(data, f)
    return 'OK', 200

@app.route('/', methods=['GET', 'POST'])
def index():
    m = folium.Map(location=[37.0902, -95.7129], zoom_start=4)  # Default to USA, will be overwritten if shapefile is loaded
    
    # Add USA base map using OpenStreetMap tiles
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}', 
                     attr='Esri', 
                     name='Esri Terrain', 
                     overlay=False, 
                     control=True).add_to(m)

    # Add draw tools
    draw = Draw(export=True)
    draw.add_to(m)

    m.save('templates/map.html')
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
    
# @app.route('/', methods=['GET', 'POST'])
# def index():
#     m = folium.Map(location=[37.0902, -95.7129], zoom_start=4)  # Default to USA, will be overwritten if shapefile is loaded
    
#     # Add USA base map using OpenStreetMap tiles
#     folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}', 
#                      attr='Esri', 
#                      name='Esri Terrain', 
#                      overlay=False, 
#                      control=True).add_to(m)

#     if request.method == 'POST':
#         filepath = request.form['filepath']
#         if filepath.endswith('.shp'):
#             gdf = gpd.read_file('/mnt/c/Users/iambh/OneDrive/Documents/MD_SHP/Maryland.shp')
            
#              # Simplify geometry
#             gdf.geometry = gdf.geometry.simplify(tolerance=0.01)
            
#             # Find the centroid of the shapefile bounds
#             gdf = gdf.to_crs(epsg = 4326)
#             bounds = gdf.total_bounds
#             center_lat = (bounds[1] + bounds[3]) / 2
#             center_lon = (bounds[0] + bounds[2]) / 2
            
#             # Update map center and zoom level
#             m.location = [center_lat, center_lon]
#             print(center_lat, center_lon)
#             m.zoom_start = 10
            
#             # Add shapefile to map with green color
#             folium.GeoJson(gdf, style_function=lambda feature: {
#                 'fillColor': 'green',
#                 'color': 'green',
#                 'weight': 2,
#                 'dashArray': '5, 5'
#             }).add_to(m)
            
#             # Fit map to bounds of shapefile with some offset
#             m.fit_bounds([[bounds[1] - 0.1, bounds[0] - 0.1], [bounds[3] + 0.1, bounds[2] + 0.1]])

#             print('done')
    
#     m.save('templates/map.html')
#     print('done')
#     return render_template('index.html')

# if __name__ == '__main__':
#     app.run(debug=True)
