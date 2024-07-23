import argparse
import subprocess
import os
import sys


# Mapping of modules and functions to their respective relative paths
script_paths = {
    "weather": {
        "download_windspeed": "weather/nldas_ws.py",
        "download_daily": "weather/download_daily.py",
        "daily2monthly": "weather/daily2monthly.py"
    },
    "soil": {
        "process_gdb": "ssurgo/processing.py",
        "fetch": "ssurgo/fetch.py"
    },
    "sites": {
        "generate": "sites/generate.py"
    },
    "workspace": {
        "prepare": "workspace/prep.py",
        "run": "workspace/run.py",
        "listfiles": "workspace/listfiles.py",
        "new": "workspace/create_ws.py",
        "add": "workspace/add.py",
        "post_process": "workspace/post_process.py",
        "visualize": "workspace/visualize.py"
    },
    "csb_utils": {
        "crop_csb": "csb_utils/crop_csb.py"
    },
}



def dispatch(module, func, options_str, wait = True):
    root_path = os.path.dirname(__file__)
    command = f'{sys.executable} {{script_path}} {options_str}'
    relative_path = script_paths.get(module, {}).get(func)
            
    if relative_path:
        script_path = os.path.join(root_path, relative_path)
    else:
        print(f"Command '{module} {func}' not found.")
        return

    env = os.environ.copy()

    command = command.format(script_path = script_path)
    if wait:
        message = subprocess.Popen(command, shell=True, env = env).wait()
    else:
        message = subprocess.Popen(command, shell=True, env = env)

def main():
    parser = argparse.ArgumentParser(description="EPIC package CLI")
    parser.add_argument('module', help='Module name')
    parser.add_argument('func', help='Function name')
    parser.add_argument('options', nargs=argparse.REMAINDER, help='Other options for the cmd')
    args = parser.parse_args()
    options_str = " ".join(args.options)
    dispatch(args.module, args.func, options_str)
    

if __name__ == '__main__':
    main()
