"""React Agent.

This module defines a custom reasoning and action agent graph.
It invokes tools in a simple loop.
"""

from docs_doctor.agent.graph import docs_doctor
from dotenv import load_dotenv
load_dotenv('./.env')
__all__ = ["docs_doctor"]
