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

default_functions = {
    "weather": "download_daily",
    "soil": "fetch",
    "sites": "generate",
    "workspace": "run",
    "csb_utils": "crop_csb"
}

def find_function(func_name):
    for module, funcs in script_paths.items():
        if func_name in funcs:
            return module, funcs[func_name]
    return None, None

def dispatch(module, func, options_str, wait=True):
    root_path = os.path.dirname(__file__)
    command = f'{sys.executable} {{script_path}} {options_str}'

    if not module:
        # Find function across all modules if no specific module is given
        module, relative_path = find_function(func)
        if not relative_path:
            print(f"Function '{func}' not found in any module.")
            return
    else:
        if not func:
            # Default to a specific function if only module is given
            func = default_functions.get(module)
        relative_path = script_paths.get(module, {}).get(func)

    if relative_path:
        script_path = os.path.join(root_path, relative_path)
    else:
        print(f"Command '{module} {func}' not found.")
        return

    env = os.environ.copy()
    command = command.format(script_path=script_path)
    if wait:
        subprocess.Popen(command, shell=True, env=env).wait()
    else:
        subprocess.Popen(command, shell=True, env=env)

def main():
    parser = argparse.ArgumentParser(description="EPIC package CLI")
    parser.add_argument('module', nargs='?', help='Module name')
    parser.add_argument('func', nargs='?', help='Function name')
    parser.add_argument('options', nargs=argparse.REMAINDER, help='Other options for the command')
    args = parser.parse_args()
    options_str = " ".join(args.options)
    
    if not args.module and args.func:
        # If module is not given but func is specified, try to find it across modules
        args.module, _ = find_function(args.func)
    
    if args.module and not args.func:
        # If module is given but func is not specified, default to predefined function
        args.func = default_functions.get(args.module)
    
    dispatch(args.module, args.func, options_str)

if __name__ == '__main__':
    main()