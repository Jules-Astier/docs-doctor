# setup.py
from setuptools import setup, find_packages

setup(
    name="docs-doctor",
    version="0.1.0",
    description="A LangGraph-based MoE agent with a package driven knowledge base.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author="Jules Astier",
    author_email="astier.jules@gmail.com",
    license="LICENSE",
    python_requires=">=3.12",
    packages=find_packages(where='src',include=['docs_doctor']),
    
    install_requires=[
        "langgraph>=0.2.6",
        "langchain-openai>=0.1.22",
        "langchain-anthropic>=0.1.23",
        "langchain>=0.2.14",
        "langchain-fireworks>=0.1.7",
        "python-dotenv>=1.0.1",
        "langchain-community>=0.2.17",
        "tavily-python>=0.4.0",
        "supabase>=2.12.0",
        "fastapi",
        "streamlit",
        "langchain-google-genai~=2.0.5",
        "langchain-groq~=0.2.1",
        "langchain-aws~=0.2.7",
        "pydantic~=2.10.1",
        "pydantic-settings~=2.6.1",
        "setuptools~=75.6.0",
        "langgraph-checkpoint-sqlite>=2.0.1",
    ],
    
    extras_require={
        'dev': [
            "mypy>=1.11.1",
            "ruff>=0.6.1",
            "pytest",
            "pytest-cov"
        ],
    },
    
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],

    # Additional configuration for pytest
    options={
        'test': {
            'pytest': {
                'addopts': '-v --cov=src',
                'testpaths': ['tests'],
            },
        },
    },
)