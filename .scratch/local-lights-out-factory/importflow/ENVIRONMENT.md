# Prepared Python environment

Python 3.11. Runtime FastAPI 0.141.1 and uvicorn 0.52.4. Tests have pytest 9.1.1
and httpx 0.28.1. Include exactly fastapi==0.141.1 and uvicorn==0.52.4 as project
runtime dependencies. setuptools and wheel are preinstalled. Installed commands
are invoked via Python in writable noexec sandbox folders. Dependencies are
preinstalled; model work has no network or package installation tools.
