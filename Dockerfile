FROM ghcr.io/astral-sh/uv:debian
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Configure the Python directory so it is consistent
ENV UV_PYTHON_INSTALL_DIR=/python

# Only use the managed Python version
ENV UV_PYTHON_PREFERENCE=only-managed

# Install Python before the project for caching
RUN uv python install 3.13

WORKDIR /app
ADD . /app
RUN uv sync --dev
RUN uv run scrapling install
RUN uv run playwright install-deps
RUN uv run playwright install
RUN uv run camoufox
