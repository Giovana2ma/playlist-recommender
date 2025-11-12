# Dockerfile for Frontend Container - REST API Server
# This container runs the Flask API server for playlist recommendations
# It does NOT include the generated rules - those will be mounted as a volume

FROM python:3.9-slim-bullseye

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy only the server code (NOT the model/rules file)
COPY server.py .

# Create directory for model files (will be mounted)
RUN mkdir -p /model

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MODEL_PATH=/model/rules.pkl
ENV API_VERSION=1.0.0
ENV API_PORT=5000

# Expose the Flask port
EXPOSE 5000

# Run Flask server
# Listen on all addresses (0.0.0.0) to accept connections from outside the container
CMD ["python", "server.py"]
