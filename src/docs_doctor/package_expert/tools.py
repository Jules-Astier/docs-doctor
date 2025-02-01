"""This module provides example tools for web scraping and search functionality.

It includes a basic Tavily search function (as an example)

These tools are intended as free examples to get started. For production use,
consider implementing more robust and specialized tools tailored to your needs.
"""

from typing import Any, Callable, List

from langchain_core.tools import InjectedToolArg
from typing_extensions import Annotated
from langgraph.types import Command

from src.docs_doctor.utils import embedding_model, supabase

async def get_embedding(
    text: str,
) -> List[float]:
    """Get embedding vector from OpenAI."""
    try:
        response = await embedding_model.embed_query(text)
        return response
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return [0] * 1536  # Return zero vector on error

async def retrieve_relevant_documentation(
    user_query: str,
    *,
    package_name: Annotated[str, InjectedToolArg],
) -> Command:
    """
    Retrieve relevant documentation chunks based on the query with RAG.
    """
    try:
        # Get the embedding for the query
        query_embedding = await get_embedding(user_query)
        
        # Query Supabase for relevant documents
        result = supabase.rpc(
            'match_site_pages',
            {
                'query_embedding': query_embedding,
                'match_count': 5,
                'filter': {'source': f"{package_name}"}
            }
        ).execute()
        
        if not result.data:
            return "No relevant documentation found."
            
        # Format the results
        formatted_chunks = []
        for doc in result.data:
            chunk_text = f"""
# {doc['title']}

{doc['content']}
"""
            formatted_chunks.append(chunk_text)
            
        # Join all chunks with a separator
        return "\n\n---\n\n".join(formatted_chunks)
        
    except Exception as e:
        print(f"Error retrieving documentation: {e}")
        return f"Error retrieving documentation: {str(e)}"

async def list_documentation_pages(
    *,
    package_name: Annotated[str, InjectedToolArg],
) -> Command:
    """
    Retrieve a list of all available Package documentation pages.
    """
    try:
        # Query Supabase for unique URLs where source is pydantic_ai_docs
        result = supabase.from_('site_pages') \
            .select('url') \
            .eq('metadata->>source', f"{package_name}") \
            .execute()
        
        print('PACKAGE NAME: ', package_name)
        print('RESULT: ', result)

        
        if not result.data:
            return []
            
        # Extract unique URLs
        urls = sorted(set(doc['url'] for doc in result.data))
        return urls
        
    except Exception as e:
        print(f"Error retrieving documentation pages: {e}")
        return []

async def get_page_content(
	url: str,
	*,
    package_name: Annotated[str, InjectedToolArg],
) -> Command:
    """
    Retrieve the full content of a specific documentation page using it's url by combining all its chunks.
    """
    try:
        # Query Supabase for all chunks of this URL, ordered by chunk_number
        result = supabase.from_('site_pages') \
            .select('title, content, chunk_number') \
            .eq('url', url) \
            .eq('metadata->>source', f"{package_name}") \
            .order('chunk_number') \
            .execute()
        
        if not result.data:
            return f"No content found for URL: {url}"
            
        # Format the page with its title and all chunks
        page_title = result.data[0]['title'].split(' - ')[0]  # Get the main title
        formatted_content = [f"# {page_title}\n"]
        
        # Add each chunk's content
        for chunk in result.data:
            formatted_content.append(chunk['content'])
            
        # Join everything together
        return "\n\n".join(formatted_content)
        
    except Exception as e:
        print(f"Error retrieving page content: {e}")
        return f"Error retrieving page content: {str(e)}"

TOOLS: List[Callable[..., Any]] = [
    retrieve_relevant_documentation,
    list_documentation_pages,
    get_page_content,
]
