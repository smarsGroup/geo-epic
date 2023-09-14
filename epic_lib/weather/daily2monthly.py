import os
import argparse
from epic_io import DLY

parser = argparse.ArgumentParser(description="Daily to Monthly")
parser.add_argument("-i", "--input", required = True, help="Path to the input file or folder")
parser.add_argument("-o", "--output", help = "Path to the output folder (optional)")
args = parser.parse_args()

output_folder = args.output if args.output else "./Monthly"
os.makedirs(output_folder, exist_ok=False)

def convert_file(file_path):
    dly = DLY(file_path)
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    dly.to_monthly(os.path.join(output_folder, file_name))

def process_folder(folder_path):
    file_list = os.listdir(folder_path)
    for file_name in file_list:
        file_path = os.path.join(folder_path, file_name)
        convert_file(file_path)
        
if os.path.isfile(args.input):
    convert_file(args.input)
elif os.path.isdir(args.input):
    process_folder(args.input)
else:
    print("Invalid input. Please provide a valid file or folder path.")

