FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set proper permissions for service account key
RUN chmod 600 /app/rhea-app-sa-key.json

# Set environment variable
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/rhea-app-sa-key.json

# Run the batch processor
CMD ["python", "batch_processor.py"] 