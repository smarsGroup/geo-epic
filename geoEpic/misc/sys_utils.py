import signal
import time
import os
import sys
import importlib.util
import shutil
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import threading
from threading import Timer


def run_with_timeout(func, timeout, *args, **kwargs):
    """
    Executes a function with a timeout using signals (not recommended).

    Args:
      func: The function to execute.
      timeout: The maximum execution time in seconds.
      *args: Arguments to pass to the function.
      **kwargs: Keyword arguments to pass to the function.

    Returns:
      The result of the function if it finishes within the timeout.

    Raises:
      TimeoutError: If the function execution exceeds the timeout.
    """
    def handler(signum, frame):
        raise TimeoutError("Execution timed out")

    original_signal = signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)

    try:
        result = func(*args, **kwargs)
    finally:
        signal.signal(signal.SIGALRM, original_signal)
        signal.alarm(0)  # Cancel any pending alarms

    return result
    
    
def parallel_executor(func, args, method='Process', max_workers=10, return_value=False, bar=True, timeout=None):
    """
    Executes a function across multiple processes and collects the results.

    Args:
        func: The function to execute.
        method: string as Process or Thread.
        args: An iterable of arguments to pass to the function.
        max_workers: The maximum number of processes to use.
        return_value: A boolean indicating whether the function returns a value.
        timeout: Number of seconds to wait for a process to complete

    Returns:
        results: If return_value is True, a list of results from the function executions sorted according to 
                 If return_value is False, an empty list is returned.
        failed_indices: A list of indices of arguments for which the function execution failed.
    """

    failed_indices = []
    results = [None] * len(args) if return_value else []
    PoolExecutor = {'Process': ProcessPoolExecutor, 'Thread': ThreadPoolExecutor}[method]
    
    with PoolExecutor(max_workers=max_workers) as executor:
        if bar: pbar = tqdm(total=len(args))

        if method == 'Process' and timeout is not None:
            futures = {executor.submit(run_with_timeout, func, timeout, arg): i for i, arg in enumerate(args)}
        else:
            futures = {executor.submit(func, arg): i for i, arg in enumerate(args)}
        
        try:
            for future in as_completed(futures):
                ind = futures[future]
                if future.exception() is not None:
                    print(f'\nFunction execution failed for args:\n {args[ind]}')
                    print(f'Exception: {future.exception()}.\n')
                    failed_indices.append(ind)
                elif return_value:
                    results[ind] = future.result()
                if bar: pbar.update(1)
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt caught, canceling remaining operations...")
            for future in futures.keys():
                future.cancel()
        finally:
            if bar: pbar.close()
    
    return results, failed_indices


def import_function(cmd = None):
    """
    Loads a function from a module based on a path and function name specified in the config.
    
    Args:
        cmd (str): "/path/to/module.py function_name".

    Returns:
        function: The loaded function, or None if not found.
    """
    if cmd is None: return None

    path, function_name = cmd.split()

    # Ensure the path is in the right format and loadable
    module_name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(module_name, path)

    if spec is None:
        print(f"Cannot find module {path}")
        return None

    # Load the module
    try:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"Error loading module: {e}")
        return None

    # Get the function and return it
    if hasattr(module, function_name):
        return getattr(module, function_name)
    else:
        print(f"Function {function_name} not found in {path}")
        return None
    


def check_disk_space(output_dir, est, safety_margin=0.1):
    """
    Checks whether there is sufficient disk space available for saving output files.

    Args:
        output_dir (str): Directory where files will be saved.
        config (dict): Configuration dictionary with an "output_types" key.
        safety_margin (float): The safety margin to add to the estimated disk usage (default is 10%).

    Raises:
        Exception: If the free disk space is lower than the estimated required space.
    """
    # Retrieve disk space details for the specified output directory
    total_bytes, used_bytes, free_bytes = shutil.disk_usage(output_dir)
    
    # Convert free bytes to GiB for easy reading
    free_gib = free_bytes // (1024**3)

    # Adjust for the safety margin
    estimated_required_gib = int(est * (1 + safety_margin))

    # Check if there is sufficient free disk space
    if free_gib < estimated_required_gib:
        message = (f"Insufficient disk space in '{output_dir}'. Estimated required: {est} GiB, "
                   f"Available: {free_gib} GiB. Consider using the 'Process Outputs' option.")
        raise Exception(message)