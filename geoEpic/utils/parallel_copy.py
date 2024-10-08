import os
import shutil
import glob
import argparse
from parallel import parallel_executor
from tqdm import tqdm
import subprocess

def rsync_copy(src_dst):
    os.makedirs(os.path.dirname(src_dst[1]), exist_ok=True)
    rsync_command = ["rsync", "-a"]  # Use archive mode for preserving attributes
    rsync_command.extend(src_dst)
    subprocess.run(rsync_command, check=True)

def parallel_copy(source_dir, destination_dir, max_workers=4, extension=None, level_one=False, exclude_dirs=False, progress_bar=True):
    """
    Copy files from source to destination directory using parallel processing.

    Args:
        source_dir (str): Path to the source directory.
        destination_dir (str): Path to the destination directory.
        max_workers (int): Number of parallel workers to use.
        extension (str): Specific file extension to filter (e.g., ".txt").
        level_one (bool): If True, only copy files from the top-level directory.
        exclude_dirs (bool): If True, exclude directories from the copying process.
        progress_bar (bool): Show a progress bar if True.
    """
    # Define the glob pattern based on the provided options
    if level_one:
        # Only get files in the top level (non-recursive)
        pattern = os.path.join(source_dir, '*')
    else:
        # Recursively get all files and directories
        pattern = os.path.join(source_dir, '**')

    # Use glob to find matching files based on the pattern
    file_paths = glob.glob(pattern, recursive=not level_one)

    # Filter out files based on the extension and exclude directories if requested
    file_pairs = [
        (src, os.path.join(destination_dir, os.path.relpath(src, source_dir)))
        for src in file_paths
        if (os.path.isfile(src) or not exclude_dirs) and (not extension or src.endswith(extension))
    ]
    parallel_executor(rsync_copy, file_pairs, 
                      method = 'Thread', max_workers = max_workers,
                      timeout = 20, bar = progress_bar)


def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Parallel file copy from source to destination.")
    parser.add_argument("source", help="Path to the source directory")
    parser.add_argument("destination", help="Path to the destination directory")
    parser.add_argument("-w", "--max-workers", type=int, default=10, help="Number of parallel workers to use (default: 10)")
    parser.add_argument("-e", "--extension", type=str, help="Copy only files with the specified extension (e.g., '.txt')")
    parser.add_argument("-l", "--level-one", action="store_true", help="Only copy files from the top-level directory")
    parser.add_argument("-x", "--exclude-dirs", action="store_true", help="Exclude directories from being copied")
    parser.add_argument("-np", "--no-progress", action="store_true", help="Do not show a progress bar")

    # Parse arguments
    args = parser.parse_args()

    # Run the parallel copy function with the parsed arguments
    parallel_copy(
        source_dir=args.source,
        destination_dir=args.destination,
        max_workers=args.max_workers,
        extension=args.extension,
        level_one=args.level_one,
        exclude_dirs=args.exclude_dirs,
        progress_bar=not args.no_progress
    )

if __name__ == "__main__":
    main()
