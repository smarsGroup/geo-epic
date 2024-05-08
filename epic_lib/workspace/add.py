import os
import shutil
import argparse

def copy_item(source_item):
    target_dir = os.getcwd()
    
    # Ensure the source_item exists
    if not os.path.exists(source_item):
        print(f"Error:'{source_item} not found.")
        return
        
    item = (source_item.split('/'))[-1]
    target_item = os.path.join(target_dir, item)
    
    if os.path.isdir(source_item):
        shutil.copytree(source_item, target_item, dirs_exist_ok=True)
    else:
        shutil.copy2(source_item, target_item)

    print(f"{item} copied to workspace ")

def main():
    parser = argparse.ArgumentParser(description="Add Utilities to EPIC Workspace")
    parser.add_argument('-f', '--files', required=True, help='Files to add to this workspace (calibration, epic_editor)')
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.dirname(__file__))
    if args.files == 'epic_editor':
        template_path = os.path.join(script_dir, "templates/EPICeditor.xlsm")
        copy_item(template_path)
    else: 
        # template_path = os.path.join(script_dir, "templates/calibration")
        copy_item(os.path.join(script_dir, "templates/calibration/calibration.py"))
        copy_item(os.path.join(script_dir, "templates/calibration/Parms_Info"))
    
    

if __name__ == '__main__':
    main()
