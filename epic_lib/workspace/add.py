import os
import shutil
import argparse

def create(template_dir):
    # if not os.path.exists(target_dir):
    #     os.makedirs(target_dir, exist_ok = True)
    target_dir = os.getcwd()
    # os.chdir(target_dir)
    # Ensure the template directory exists
    if not os.path.exists(template_dir):
        print(f"Error:'{template_dir}' not found.")
        return
    
    if os.path.isdir(template_dir):
        # Copy the content of the template directory to the target directory
        for item in os.listdir(template_dir):
            source_item = os.path.join(template_dir, item)
            target_item = os.path.join(target_dir, item)

            if os.path.isdir(source_item):
                shutil.copytree(source_item, target_item)
            else:
                # if source_item.split('.')[-1] != 'py':
                shutil.copy2(source_item, target_item)
    else:
        item = (template_dir.split('/'))[-1]
        target_item = os.path.join(target_dir, item)
        shutil.copytree(template_dir, target_item)

    print(f"{target_dir} copied to workspace ")

def main():
    parser = argparse.ArgumentParser(description="Create Workspace for EPIC package")
    parser.add_argument('-f', '--files', required=True, help='Files to add to this workspace (calibration, epic_editor)')
    args = parser.parse_args()

    # Assuming your template directory is located at "./ws_template" relative to the script
    script_dir = os.path.dirname(os.path.dirname(__file__))
    if args.files == 'epic_editor':
        template_path = os.path.join(script_dir, "templates/EPICeditor.xlsm")
    else: 
        template_path = os.path.join(script_dir, "templates/calibration")
    
    create(template_path)

if __name__ == '__main__':
    main()
