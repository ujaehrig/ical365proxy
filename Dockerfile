FROM python:3.13-slim
# Install UV
COPY --from=ghcr.io/astral-sh/uv@sha256:2381d6aa60c326b71fd40023f921a0a3b8f91b14d5db6b90402e65a635053709 /uv /uvx /bin/

# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

# Copy the project into the image
COPY uv.lock pyproject.toml main.py  timezone.csv /app

# Sync the project into a new environment, using the frozen lockfile
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen
#RUN uv venv
#RUN uv pip install .

# Expose the port
EXPOSE 5000

# Run the application
CMD ["uv", "run", "main.py"]
