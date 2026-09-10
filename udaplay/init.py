"""
UdaPlay environment setup — run this once before the notebooks.

    python init.py

Installs the required dependencies and verifies the environment is ready.
"""

import subprocess
import sys
import os

PACKAGES = [
    "chromadb>=1.0.4",
    "openai>=1.73.0",
    "pydantic>=2.11.3",
    "python-dotenv>=1.1.0",
    "tavily-python>=0.5.4",
]

def pip_install(packages):
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", *packages])
    print("Done.\n")

def check_config():
    from dotenv import load_dotenv
    load_dotenv("config.env")

    openai_key = os.getenv("OPENAI_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")

    print("=== API Key Status ===")

    if openai_key:
        print(f"  OPENAI_API_KEY  : set ({openai_key[:12]}...)")
    else:
        print("  OPENAI_API_KEY  : NOT SET  ← add to config.env")

    if tavily_key:
        print(f"  TAVILY_API_KEY  : set ({tavily_key[:12]}...)")
    else:
        print("  TAVILY_API_KEY  : NOT SET  ← add to config.env")

    if not openai_key:
        print("\n  ERROR: OPENAI_API_KEY is required in config.env")
        sys.exit(1)
    if not tavily_key:
        print("\n  ERROR: TAVILY_API_KEY is required — get a free key at https://tavily.com")
        sys.exit(1)

    print()

def smoke_test():
    print("=== Import Check ===")
    failures = []
    for module, pkg in [
        ("chromadb", "chromadb"),
        ("openai",   "openai"),
        ("pydantic", "pydantic"),
        ("dotenv",   "python-dotenv"),
        ("tavily",   "tavily-python"),
    ]:
        try:
            __import__(module)
            print(f"  {module:<12} OK")
        except ImportError:
            print(f"  {module:<12} MISSING")
            failures.append(pkg)

    if failures:
        print(f"\n  Run: pip install {' '.join(failures)}")
        sys.exit(1)
    print()

if __name__ == "__main__":
    pip_install(PACKAGES)
    smoke_test()
    check_config()
    print("Environment ready. Open Udaplay_01_solution_project.ipynb to begin.")
