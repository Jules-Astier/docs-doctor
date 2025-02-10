import click
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

@click.group()
def cli():
    """Command line interface for docs-doctor"""
    pass

@cli.command()
@click.option(
    "--host",
    default="localhost",
    help="Host to run the Streamlit app on",
    show_default=True,
)
@click.option(
    "--port",
    default=8501,
    help="Port to run the Streamlit app on",
    show_default=True,
)
def serve(host: str, port: int):
    """Run the app locally using Streamlit"""
    # Original local server logic
    current_dir = Path(__file__).parent
    streamlit_app = current_dir / "streamlit.py"
    
    if not streamlit_app.exists():
        click.echo(f"Error: Could not find streamlit.py in {current_dir}", err=True)
        sys.exit(1)
    
    env = os.environ.copy()
    env["STREAMLIT_SERVER_PORT"] = str(port)
    env["STREAMLIT_SERVER_ADDRESS"] = host
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    env["STREAMLIT_CLIENT_TOOLBAR_MODE"] = "minimal"
    
    click.echo(f"Starting Streamlit app on http://{host}:{port}")
    
    try:
        subprocess.run(
            [
                "streamlit",
                "run",
                str(streamlit_app),
                "--server.address",
                host,
                "--server.port",
                str(port),
                "--logger.level",
                "info",
            ],
            env=env,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        click.echo(f"Error running Streamlit app: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nShutting down Streamlit app")
        sys.exit(0)


if __name__ == "__main__":
    cli()