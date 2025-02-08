from utils import supabase
from pathlib import Path
import tomli  # for pyproject.toml
import re
from typing import Dict, List, Optional, Set


def get_available_packages():
	try:
		result = supabase.from_('packages') \
					.select('*') \
					.execute()
		packages = result.data
		# packages = supabase.fetch_all("SELECT * FROM packages")
		return packages
	except:
		print("UNABLE TO FETCH PACKAGES FROM SUPABASE")
		return []

def get_local_packages(project_path: str | Path = None) -> List[str]:
    """
    Get a simple list of all packages used in the project.
    Combines dependencies from requirements.txt and pyproject.toml.
    """
    if project_path is None:
        project_path = Path.cwd()
    else:
        project_path = Path(project_path)

    all_packages: Set[str] = set()
    
    # Check requirements.txt
    req_file = project_path / 'requirements.txt'
    if req_file.exists():
        with open(req_file, 'r') as f:
            for line in f:
                # Skip comments and empty lines
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Skip include statements and options
                if line.startswith(('-r', '--requirement', '-')):
                    continue
                
                # Extract package name (remove version specifiers and extras)
                package = re.split(r'[=<>!~\[\s]', line)[0]
                if package:
                    all_packages.add(package)
    
    # Check pyproject.toml
    pyproject = project_path / 'pyproject.toml'
    if pyproject.exists():
        try:
            with open(pyproject, 'rb') as f:
                data = tomli.load(f)
            
            # Check Poetry dependencies
            if 'tool' in data and 'poetry' in data['tool']:
                poetry = data['tool']['poetry']
                if 'dependencies' in poetry:
                    all_packages.update(poetry['dependencies'].keys())
            
            # Check PEP 621 dependencies
            if 'project' in data and 'dependencies' in data['project']:
                deps = data['project']['dependencies']
                # Handle both string and dict formats
                for dep in deps:
                    if isinstance(dep, str):
                        package = re.split(r'[=<>!~\[\s]', dep)[0]
                        all_packages.add(package)
                    elif isinstance(dep, dict):
                        all_packages.update(dep.keys())
        
        except Exception as e:
            print(f"Error reading pyproject.toml: {e}")
    
    # Remove python-specific dependencies and empty strings
    all_packages.discard('python')
    all_packages.discard('')
    
    # Return sorted list
    return sorted(all_packages)