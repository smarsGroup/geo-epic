import argparse
import subprocess
import os

def main():
    parser = argparse.ArgumentParser(description="EPIC package CLI")
    parser.add_argument('cmd', help='Command to run')
    parser.add_argument('-c', '--config', help='Path to the config.yml file', default=None)
    parser.add_argument('-w', '--working_dir', help='Working directory', default='./')
    parser.add_argument('options', nargs=argparse.REMAINDER, help='Other options for the cmd')

    args = parser.parse_args()

    # Dispatch to the right function/script based on script_name
    env = os.environ.copy()
    root_path = os.path.dirname(__file__)
    env["PYTHONPATH"] = root_path + ":" + env.get("PYTHONPATH", "")

    # Base command
    command = f'python3 {{script_path}} {args.options}'

    if args.cmd == "download_windspeed":
        script_path = os.path.join(root_path, "weather", "nldas_ws.py")
    elif args.cmd == "process_soils":
        script_path = os.path.join(root_path, "ssurgo", "processing.py")
    elif args.cmd == "generate_site":
        script_path = os.path.join(root_path, "sit", "generate.py")
    elif args.cmd == "prep":
        script_path = os.path.join(root_path, "scripts", "prep.py")
        command += f' -c {args.config}'
    elif args.cmd == "run":
        script_path = os.path.join(root_path, "scripts", "run.py")
        command += f' -c {args.config}'
    elif args.cmd == "create_ws":
        script_path = os.path.join(root_path, "scripts", "create_ws.py")
        command = f'python3 {script_path} -w {args.working_dir}'
    else:
        print(f"Command '{args.cmd}' not found.")
        return
    
    command = command.format(script_path = script_path)
    message = subprocess.Popen(command, shell=True, env=env).wait()

if __name__ == '__main__':
    main()