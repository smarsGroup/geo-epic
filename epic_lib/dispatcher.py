import argparse
import subprocess
import os

def dispatch(module, func, options_str, wait = True):
    root_path = os.path.dirname(__file__)
    python_path = '/home/chandrab/anaconda3/envs/epic_env/bin/python'
    command = f'{python_path} {{script_path}} {options_str}'
    script_path = None
    if module == "weather":
        if func == "download_windspeed":
            script_path = os.path.join(root_path, "weather", "nldas_ws.py")
        elif func == "download_daily":
            script_path = os.path.join(root_path, "weather", "download_daily.py")
        elif func == "daily2monthly":
            script_path = os.path.join(root_path, "weather", "daily2monthly.py")
    elif module == "soil":
        if func == "process_gdb":
            script_path = os.path.join(root_path, "ssurgo", "processing.py")
    elif module == "sites":
        if func == "generate":
            script_path = os.path.join(root_path, "sites", "generate.py")
    elif module == "workspace":
        if func == "prepare":
            script_path = os.path.join(root_path, "workspace", "prep.py")
        elif func == "run":
            script_path = os.path.join(root_path, "workspace", "run.py")
        elif func == "listfiles":
            script_path = os.path.join(root_path, "workspace", "listfiles.py")
        elif func == "new":
            script_path = os.path.join(root_path, "workspace", "create_ws.py")
            
    if script_path is None:
        print(f"Command '{module} {func}' not found.")
        return
    
    command = command.format(script_path = script_path)
    if wait:
        message = subprocess.Popen(command, shell=True).wait()
    else:
        message = subprocess.Popen(command, shell=True)

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
