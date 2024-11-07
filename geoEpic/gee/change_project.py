import argparse
from core import *
from geoEpic.gee import ee_Initialize,change_project_name, change_authentication

def main():
    parser = argparse.ArgumentParser(description="change GEE  project")
    parser.add_argument('-n','--project_name', type=str, help="Specify a GEE project name to set or update.")
    parser.add_argument('-r','--reset_authentication', action='store_true',  help="Reset credentials and re-authenticate.")

    args = parser.parse_args()
    
    if args.reset_authentication:
        change_authentication()
    
    change_project_name(args.project_name)
    ee_Initialize()


if __name__ == '__main__':
    main()