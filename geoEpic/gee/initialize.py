import ee
import json
import os
from geoEpic.utils.workerpool import WorkerPool
import shutil

def ee_Initialize():
    # Get the directory where the script is located
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_FILE = os.path.join(SCRIPT_DIR, 'config.json')
    config = None
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
           config = json.load(file)
    
    if config and 'project' in config:
        project_name = config['project']
    else:
        project_name = input("Please enter the GEE project: \n")
        change_project_name(project_name)
    
    try:
        ee.Authenticate()
        ee.Initialize(project=project_name, opt_url='https://earthengine-highvolume.googleapis.com')
    except Exception as e:
        print("Authentication failed. Restarting project name and authentication.")
        project_name = input("Enter the new GEE project name: \n")
        change_project_name(project_name)
        change_authentication()
        ee.Initialize(project=project_name, opt_url='https://earthengine-highvolume.googleapis.com') 
    
    pool = WorkerPool(f'gee_global_lock_{project_name}')
    if pool.queue_len() is None: pool.open(40)
    return project_name

def change_project_name(project_name):
    config = {'project': project_name}
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_FILE = os.path.join(SCRIPT_DIR, 'config.json')
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent = 4)
    print(f"Changed the project_name to {project_name}")
    
def change_authentication():
    creds_path = ee.oauth.get_credentials_path()
    os.remove(creds_path)
    ee.Authenticate()

def ee_ReInitialize():
    project_name = input("Enter the new GEE project name: \n")
    config = {'project': project_name}
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_FILE = os.path.join(SCRIPT_DIR, 'config.json')
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent = 4)
        
    try:
        ee.Initialize(project=project_name, opt_url='https://earthengine-highvolume.googleapis.com')
        print(f"Changed the project_name to {project_name}")
    except Exception as e:
        print("Authentication required.")
        ee.Authenticate()
        ee.Initialize(project=project_name, opt_url='https://earthengine-highvolume.googleapis.com')
        # print(f"Reinitialized GEE with new project: {project_name}")