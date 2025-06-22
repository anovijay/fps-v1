#!/bin/bash

# Simple Email Extraction Batch Job Deployment
# No service account complications - uses default permissions

set -e  # Exit on any error

# Configuration
PROJECT_ID="rhea-461313"
REGION="us-central1"
JOB_NAME="data-extraction-service"
IMAGE_NAME="gcr.io/$PROJECT_ID/$JOB_NAME"

echo "🚀 Starting batch job deployment..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Job: $JOB_NAME"
echo ""

# Set project
echo "📋 Setting project..."
gcloud config set project $PROJECT_ID

# Enable APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable firestore.googleapis.com

# Clear build cache
echo "🧹 Clearing build cache..."
echo "Clearing Docker build cache..."
docker system prune -f --volumes 2>/dev/null || true
echo "Clearing gcloud build cache..."
gcloud builds list --limit=10 --format="value(id)" | xargs -I {} gcloud builds cancel {} 2>/dev/null || true

# Build container with cache busting
echo "🏗️ Building container image..."
# Add timestamp to force fresh build
BUILD_TAG="$IMAGE_NAME:$(date +%s)"
gcloud builds submit --tag $BUILD_TAG --tag $IMAGE_NAME

# Clean up existing job if it exists
echo "🗑️ Cleaning up existing job..."
gcloud run jobs delete $JOB_NAME --region=$REGION --quiet 2>/dev/null || true

# Deploy Cloud Run Job (simple version)
echo "🚀 Deploying Cloud Run Job..."
gcloud run jobs create $JOB_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --set-env-vars="GOOGLE_APPLICATION_CREDENTIALS=/app/rhea-app-sa-key.json" \
    --memory 1Gi \
    --cpu 1 \
    --task-timeout 1800 \
    --parallelism 1 \
    --tasks 1

# Clean up existing scheduler if it exists
echo "🗑️ Cleaning up existing scheduler..."
gcloud scheduler jobs delete email-extraction-scheduler --location=$REGION --quiet 2>/dev/null || true

# Create Cloud Scheduler (simple version - no service account)
echo "⏰ Setting up Cloud Scheduler..."
gcloud scheduler jobs create http email-extraction-scheduler \
    --location=$REGION \
    --schedule="*/30 * * * *" \
    --uri="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/$JOB_NAME:run" \
    --http-method=POST

# Test the job
echo "🧪 Testing job execution..."
gcloud run jobs execute $JOB_NAME --region=$REGION --wait

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📊 Summary:"
echo "   • Job: $JOB_NAME"
echo "   • Region: $REGION"
echo "   • Schedule: Every 30 minutes"
echo "   • Image: $IMAGE_NAME"
echo ""
echo "🔗 Useful commands:"
echo "   • Manual run: gcloud run jobs execute $JOB_NAME --region=$REGION"
echo "   • View logs: gcloud run jobs executions logs --job=$JOB_NAME --region=$REGION --limit=50"
echo "   • Job status: gcloud run jobs describe $JOB_NAME --region=$REGION"
echo "" 