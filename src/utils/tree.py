import os
from pathlib import Path
from typing import List, Optional

def get_directory_structure(
    root_path: str = ".",
    max_depth: Optional[int] = None,
    ignore_patterns: Optional[List[str]] = None,
    prefix: str = "",
    is_last: bool = True
) -> str:
    """
    Generate a tree-like ASCII representation of a directory structure.
    
    Args:
        root_path (str): The root directory path to start from
        max_depth (int, optional): Maximum depth to traverse. None means no limit
        ignore_patterns (List[str], optional): List of patterns to ignore
        prefix (str): Current line prefix for nested items
        is_last (bool): Whether current item is last in its parent
    
    Returns:
        str: A string containing the tree-like directory structure
    """
    if ignore_patterns is None:
        ignore_patterns = ['.git', '__pycache__', '.pytest_cache', '.venv', 'venv']
    
    def should_ignore(path: str) -> bool:
        return any(pattern in path for pattern in ignore_patterns)

    root = Path(root_path)
    structure = [root.name + "/"]
    
    try:
        # Get all items in directory, filtered and sorted
        items = sorted(
            [x for x in root.iterdir() if not should_ignore(str(x))],
            key=lambda x: (x.is_file(), x.name.lower())
        )
        
        # Calculate current depth
        current_depth = len(prefix.split("│")) - 1
        if max_depth is not None and current_depth >= max_depth:
            return f"{prefix}{'└── ' if is_last else '├── '}{root.name}/\n"
        
        # Process each item
        for i, item in enumerate(items):
            is_last_item = i == len(items) - 1
            
            # Determine the prefix for the next level
            if is_last:
                new_prefix = prefix + "    "
            else:
                new_prefix = prefix + "│   "
            
            # Add the item to the structure
            if item.is_dir():
                subdir = get_directory_structure(
                    str(item),
                    max_depth,
                    ignore_patterns,
                    new_prefix,
                    is_last_item
                )
                structure.append(subdir)
            else:
                structure.append(f"{prefix}{'└── ' if is_last_item else '├── '}{item.name}\n")
    
    except PermissionError:
        return f"{prefix}{'└── ' if is_last else '├── '}{root.name}/ (Permission denied)\n"
    except Exception as e:
        return f"{prefix}{'└── ' if is_last else '├── '}{root.name}/ (Error: {str(e)})\n"
    
    # Combine all parts
    if prefix:
        # For subdirectories
        return f"{prefix}{'└── ' if is_last else '├── '}{root.name}/\n{''.join(structure[1:])}"
    else:
        # For root directory
        return ''.join(structure)

# Example usage:
if __name__ == "__main__":
    # Print directory structure starting from current directory
    print(get_directory_structure("."))
    
    # Example with max depth
    # print(get_directory_structure(
    #     ".",
    #     max_depth=5,
    #     ignore_patterns=['.git', '__pycache__', 'node_modules']
    # ))