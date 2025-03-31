FROM python:3.13-slim

WORKDIR /app

# Install UV
COPY --from=ghcr.io/astral-sh/uv@sha256:2381d6aa60c326b71fd40023f921a0a3b8f91b14d5db6b90402e65a635053709 /uv /uvx /bin/

# Copy the project into the image
COPY pyproject.toml main.py  ./

# Sync the project into a new environment, using the frozen lockfile
WORKDIR /app
RUN uv pip install .

# Expose the port
EXPOSE 5000

# Run the application
CMD ["uv", "run", "main.py"]
