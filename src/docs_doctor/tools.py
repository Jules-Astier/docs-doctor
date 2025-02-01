"""This module provides example tools for web scraping and search functionality.

It includes a basic Tavily search function (as an example)

These tools are intended as free examples to get started. For production use,
consider implementing more robust and specialized tools tailored to your needs.
"""

from typing import Any, Callable, List

from typing_extensions import Annotated
from langgraph.types import Command
from langchain_core.tools import InjectedToolCallId, BaseTool, tool
from langchain_core.messages import ToolMessage, ChatMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from src.docs_doctor.package_expert.graph import create_package_expert
from src.docs_doctor.utils import supabase

# For testing the package experts
pydantic_ai_expert = create_package_expert('pydantic_ai')

result = supabase.from_('packages') \
            .select('*') \
            .execute()
packages = result.data

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

        # return Command(
        #     update={
        #         # update the message history
        #         "messages": [
        #             ToolMessage(
        #                 output, tool_call_id=tool_call_id
        #             )
        #         ],
        #     }
        # )
        return output
    

    
    package_expert_tool_func.__name__ = f'{package["package_name"]}_expert_tool'
    package_expert_tool_func.__doc__ = f"""Get information from the documentation the {package["package"]} python package.

        Here's a quick description of the package: {package["description"]}

        Use the query to explain what information is needed from the documentation.
        """
    package_expert_tool: BaseTool = tool(package_expert_tool_func)
    return package_expert_tool

TOOLS: List[Callable[..., Any]] = [
    create_package_expert_tool(package)
    for package in packages
]
