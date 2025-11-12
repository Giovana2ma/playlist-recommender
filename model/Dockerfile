# Dockerfile for ML Container - Rule Generation
# This container generates association rules for the playlist recommendation system
# It does NOT include the dataset - that will be mounted as a volume

FROM python:3.9-slim-bullseye

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy only the rule generation code (NOT the dataset)
COPY ruleGenerator.py .

# Create directory for output files (rules will be saved here)
RUN mkdir -p /output

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command: generate rules
# Override with specific parameters when running the container
# Example: docker run ml-container python ruleGenerator.py /data/dataset.csv -o /output/rules.pkl
ENTRYPOINT ["python", "ruleGenerator.py"]
CMD ["--help"]
