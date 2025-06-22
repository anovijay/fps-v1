FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# For production, use Workload Identity or environment-based authentication
# No service account key file needed in the container

# Run the batch processor
CMD ["python", "batch_processor.py"] 