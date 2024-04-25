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
  
    final = pd.read_csv('./yield.csv', header = None)
    final.colums = ['FieldID', 'yld']
    merged_df = shp.merge(final, on='FieldID', how='outer')
    info_df = merged_df.to_crs(epsg=3857)

    fig, ax = plt.subplots(1, 1, figsize=(20, 20))
    info_df.plot(ax=ax, column='yld', legend=True, legend_kwds={'shrink':0.4, 'aspect':100}, cmap = 'rainbow') 
    
    # Remove x and y axis visible ticks
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor('white')
    plt.title('Maryland Yield Simulation')
    plt.show()
    
