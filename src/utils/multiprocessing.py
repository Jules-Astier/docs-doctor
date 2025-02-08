from concurrent.futures import ThreadPoolExecutor

def parallel_execute(func, param_list):
    """
    Execute a function in parallel with different parameters using threads.
    
    Args:
        func: The function to execute
        param_list: List of dictionaries, where each dictionary contains parameters for one function call
        
    Returns:
        List of results from all function executions
    """
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(func, **params) for params in param_list]
        results = [future.result() for future in futures]
    return results