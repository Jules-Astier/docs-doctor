"""This module provides example tools for web scraping and search functionality.

It includes a basic Tavily search function (as an example)

These tools are intended as free examples to get started. For production use,
consider implementing more robust and specialized tools tailored to your needs.
"""

import os
from pathlib import Path
from typing import Any, Callable, List

from typing_extensions import Annotated
from langgraph.types import Command
from langchain_core.tools import InjectedToolCallId, BaseTool, tool
from langchain_core.messages import ToolMessage, ChatMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from src.agent.package_expert.graph import create_package_expert
from src.utils.packages import get_available_packages
from src.utils.tree import get_directory_structure

# For testing the package experts
pydantic_ai_expert = create_package_expert('pydantic_ai')

def create_package_expert_tool(package):
    """Create a package expert tool for a package."""
    async def package_expert_tool_func(
        query: str,
        *,
        tool_call_id: Annotated[str, InjectedToolCallId],
        config: RunnableConfig
    ):
        """Get information from the documentation of a given package."""
        
        package_expert = create_package_expert(package["package_name"])

        result = await package_expert.ainvoke({
            "messages": [
                ChatMessage(
                    content=query,
                    role='custom',
                    custom_data={
                        package_expert: package['package']
                    }
                )
            ]
        })
        
        output = result['messages'][-1].content

        return output
    

    
    package_expert_tool_func.__name__ = f'{package["package_name"]}_expert_tool'
    package_expert_tool_func.__doc__ = f"""Get information from the documentation the {package["package"]} python package.

        Here's a quick description of the package: {package["description"]}

        Use the query to explain what information is needed from the documentation.
        """
    package_expert_tool: BaseTool = tool(package_expert_tool_func)
    return package_expert_tool

async def get_project_structure() -> Command:
    """
    Retrieve the file strucutre of the local project.
    """
    try:
        tree = get_directory_structure()
        return tree
        
    except Exception as e:
        print(f"Error retrieving directory structure: {e}")
        return "Error retrieving directory structure"

async def get_file_content(
	path: str,
) -> Command:
    """
    Read content from a text file (.env, .py, .txt, .yml, .json, etc.)
    
    Args:
        path: path to file starting from the root of the project (must start with ./)

    Returns:
        str: Content of the file
    """
    try:
        file_path = Path(path).resolve()
        if not file_path.is_file():
            return "File not found: {file_path}"
        
        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            return f"Cannot read file: {file_path}"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # If UTF-8 fails, try with default system encoding
            with open(file_path, 'r') as f:
                return f.read()
        
    except Exception as e:
        print(f"Error retrieving file content: {e}")
        return f"Error retrieving file content: {str(e)}"
    
def find_file_locations(
    filename: str,
) -> List[str]:
    """
    Find all possible locations of a file in a project directory.
    
    Args:
        filename (str): Name of the file to search for
    
    Returns:
        List[str]: List of absolute paths where the file was found
    """
    # Set default values
    search_dir = os.getcwd()
    ignore_dirs = ['.git', 'node_modules', 'venv', '__pycache__', '.idea']
    
    found_locations = []
    search_path = Path(search_dir).resolve()
    
    try:
        # Walk through directory tree
        for root, dirs, files in os.walk(search_path):
            # Remove ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            # Check if the file exists in current directory
            if filename in files:
                found_path = Path(root) / filename
                found_locations.append(str(found_path.absolute()))
                
    except PermissionError as e:
        print(f"Permission denied accessing some directories: {e}")
    except Exception as e:
        print(f"An error occurred while searching: {e}")
    
    return found_locations


def select_tools(package_names: List[str] | None = None) -> List[Callable[..., Any]]:
    if package_names:
        TOOLS: List[Callable[..., Any]] = [
            create_package_expert_tool(package)
            for package in get_available_packages()
            if package['package_name'] in package_names
        ] + [
            get_project_structure,
            get_file_content,
        ]
    else:
        TOOLS: List[Callable[..., Any]] = [
        get_project_structure,
        get_file_content,
        find_file_locations,
    ]

    return TOOLS


