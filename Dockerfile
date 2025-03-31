FROM python:3.13-slim

WORKDIR /app

# Install UV
RUN pip install uv

# Copy the application
COPY main.py .

# Install dependencies using UV
RUN uv pip install ./main.py

# Expose the port
EXPOSE 5000

# Run the application
CMD ["python", "main.py"]
