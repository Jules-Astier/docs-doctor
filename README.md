# Package-MoE

A Mixture of Experts (MoE) agent built on LangGraph for answering questions about Python packages, specifically designed to handle packages released or updated after typical LLM training cutoff dates.

## Overview

Package-MoE is a specialized question-answering system that combines multiple expert agents to provide accurate, up-to-date information about Python packages. Built using LangGraph's workflow architecture, it maintains current knowledge through a managed update process.

## Features

- Real-time package information retrieval
- Specialized experts for different package domains (Web Frameworks, Data Science, DevOps, etc.)
- Router system for directing questions to appropriate experts
- Confidence scoring and multi-expert consensus for complex queries
- Regular updates to package knowledge base
- Support for package version comparisons and migration guides

## Installation

```bash
pip install package-moe
```

## Quick Start

```python
from package_moe import PackageMoE

# Initialize the agent
agent = PackageMoE()

# Ask a question about any package
response = agent.query("What are the breaking changes in FastAPI 0.109.0?")
print(response)

# Get package comparison
comparison = agent.compare_versions("fastapi", "0.108.0", "0.109.0")
print(comparison)
```

## Configuration

The agent can be configured through environment variables or a config file:

```python
from package_moe import PackageMoE

agent = PackageMoE(
    config_path="config.yaml",
    update_frequency="daily",
    expert_threshold=0.85,
    consensus_required=2
)
```

## Adding New Package Support

To request support for a new package:

1. Open an issue on our GitHub repository using the "New Package Request" template
2. Provide the following information:
   - Package name and PyPI link
   - Brief description of the package
   - Current version and release date
   - Link to official documentation
   - Any specific versioning quirks or important notes
   - (Optional) Example questions you'd like the agent to answer

Alternatively, you can submit a pull request:

1. Fork the repository
2. Add package metadata to `package_registry.yaml`
3. Create expert rules in `experts/rules/`
4. Add test cases in `tests/packages/`
5. Submit a pull request with your changes

## Architecture

Package-MoE uses a multi-layer architecture:

1. **Query Router**: Analyzes incoming questions and routes them to appropriate experts
2. **Expert Agents**: Specialized agents for different package domains
3. **Knowledge Base**: Regularly updated package information
4. **Consensus Manager**: Combines and validates expert responses
5. **Update Manager**: Handles package information updates

# CLI Commands for `docs-doctor`

## Command Group

- **`cli`**: Command line interface for docs-doctor.

## Commands

1. **`serve`**
   - **Description**: Serves the Streamlit app.
   - **Options**:
     - `--host`:
       - **Default**: `localhost`
       - **Help**: Host to run the Streamlit app on.
     - `--port`:
       - **Default**: `8501`
       - **Help**: Port to run the Streamlit app on.

## Usage Example

To run the Streamlit app, use the following command in your terminal:

```bash
python cli.py serve --host <your_host> --port <your_port>

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Setting up the development environment
- Adding new experts
- Improving routing rules
- Adding test cases
- Submitting pull requests

<!-- ## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. -->

## Contact

- GitHub Issues: [Create an issue](https://github.com/yourusername/package-moe/issues)
- Email: support@package-moe.dev
<!-- - Discord: [Join our community](https://discord.gg/package-moe) -->

<!-- ## Acknowledgments

- LangGraph team for the workflow framework
- All package maintainers who help keep documentation updated
- Our contributors and the open source community -->
```
