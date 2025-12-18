"""CLI entrypoint for kGPT."""

import subprocess
import sys
from pathlib import Path


def main():
    """Main CLI entrypoint - launches the Streamlit app."""
    # Get the path to the Streamlit app
    app_path = Path(__file__).parent / "ui" / "app.py"

    # Launch Streamlit
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path), "--server.port=8501"],
        check=True,
    )


if __name__ == "__main__":
    main()
