import argparse
import subprocess
import os

def main():
    parser = argparse.ArgumentParser(description="EPIC package CLI")
    parser.add_argument('cmd', help='Command to run')
    parser.add_argument('options', nargs=argparse.REMAINDER, help='Other options for the cmd')

    args = parser.parse_args()

    # Dispatch to the right function/script based on script_name
    env = os.environ.copy()
    root_path = os.path.dirname(__file__)
    env["PYTHONPATH"] = root_path + ":" + env.get("PYTHONPATH", "")

    # Base command
    options_str = " ".join(args.options)
    command = f'python3 {{script_path}} {options_str}'
    
    if args.module == "weather":
        if args.func == "download_windspeed":
            script_path = os.path.join(root_path, "weather", "nldas_ws.py")
        elif args.func == "download_daily":
            script_path = os.path.join(root_path, "weather", "download_daily.py")
        elif args.func == "daily2monthly":
            script_path = os.path.join(root_path, "weather", "daily2monthly.py")
    elif args.module == "soil":
        if args.func == "process_gdb":
            script_path = os.path.join(root_path, "ssurgo", "processing.py")
    elif args.module == "sites":
        if args.func == "generate":
            script_path = os.path.join(root_path, "sites", "generate.py")
    elif args.module == "workspace":
        if args.func == "prepare":
            script_path = os.path.join(root_path, "workspace", "prep.py")
        elif args.func == "run":
            script_path = os.path.join(root_path, "workspace", "run.py")
        elif args.func == "listfiles":
            script_path = os.path.join(root_path, "workspace", "listfiles.py")
        elif args.func == "new":
            script_path = os.path.join(root_path, "workspace", "create_ws.py")
    else:
        print(f"Command '{args.cmd}' not found.")
        return
    
    command = command.format(script_path = script_path)
    message = subprocess.Popen(command, shell=True, env=env).wait()

if __name__ == '__main__':
    main()