from epic_lib.io import ACY, DGN
from glob import glob
import fcntl
import os

def reduce_outputs(run_id, base_dir):
  # dgn = DGN(f'{run_id}.DGN')  
  # nee = dgn.get_var('NEE')
  
  acy = ACY(f'{run_id}.ACY')  
  yld = acy.get_var('YLDG')
  last_year = np.round(yld.iloc[-1]['YLDG'], 2)

  with open(f'{base_dir}/yield.csv', 'a') as f:
    fcntl.flock(f, fcntl.LOCK_EX)  # Exclusive lock
    f.write(f'{run_id}, {yld}\n')
    fcntl.flock(f, fcntl.LOCK_UN)  # Release lock

  
def plot():
    fp = './CropRotations/MDRotFilt1.shp'
    shp = gpd.read_file(fp)
    merged_df = shp.merge(final, on='FieldID', how='outer')
    info_df = merged_df.to_crs(epsg=3857)
    
    # states_us = gpd.read_file("../cb_2022_24_cousub_500k.shp")
    # states_us = states_us.to_crs(epsg=3857)
    
    fig, ax = plt.subplots(1, 1, figsize=(20, 20))
    
    # states_us.plot(ax=ax, color='k', linewidth=0.5, alpha = 0.9) 
    info_df.plot(ax=ax, column='Yield', legend=True, legend_kwds={'shrink':0.4, 'aspect':100}, cmap = 'rainbow') 
    # ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, alpha = 0.9)
    
    # Remove x and y axis visible ticks
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor('white')
    plt.title('Maryland Yield Simulation')
    plt.show()
    
