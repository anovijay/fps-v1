#!/bin/bash

echo "🧪 Testing Firestore Batch Processor locally..."

# Check if service account key exists
if [ ! -f "rhea-app-sa-key.json" ]; then
    echo "❌ Service account key file not found: rhea-app-sa-key.json"
    echo "Please ensure the service account key file is present in the current directory."
    exit 1
fi

# Set Google Cloud credentials
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/rhea-app-sa-key.json"

echo "✅ Google Cloud credentials configured"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Run the batch processor
echo "🚀 Running batch processor..."
python batch_processor.py

echo "✅ Local test completed!"
echo "☁️ Check Google Cloud Storage bucket 'rhea_incoming_emails' for the uploaded data"
echo "📁 Data should be in: gs://rhea_incoming_emails/firestore_data/mail_register.json" 