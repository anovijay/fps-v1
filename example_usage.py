#!/usr/bin/env python3
"""
Example usage of the refactored Email Batch Processing System

This script demonstrates how to use the new adapter-integrated batch processor
that uploads attachments to GCS, calls the LLM adapter service, and saves results.
"""

import os
import logging
from batch_processor import BatchProcessor
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Example usage of the batch processor
    """
    
    # Option 1: Use default configuration from Config class
    logger.info("🚀 Example 1: Using default configuration")
    processor = BatchProcessor()
    
    # Option 2: Override adapter service URL
    logger.info("🚀 Example 2: Using custom adapter service URL")
    custom_adapter_url = "https://my-llm-adapter-service.run.app"
    processor_custom = BatchProcessor(adapter_service_url=custom_adapter_url)
    
    # Run the batch processing
    logger.info("📋 Starting batch processing...")
    
    try:
        success = processor.process_batch()
        
        if success:
            logger.info("✅ Batch processing completed successfully!")
            
            # The processor has:
            # 1. Fetched emails with "Scheduled for Extraction" status
            # 2. Uploaded attachments to Google Cloud Storage
            # 3. Called the adapter service with the email data
            # 4. Saved extraction results to Firestore
            # 5. Updated email statuses to "Extracted"
            
        else:
            logger.error("❌ Batch processing failed!")
            
    except Exception as e:
        logger.error(f"💥 Error during batch processing: {e}")

def demonstrate_configuration():
    """
    Demonstrate how to configure the system using environment variables
    """
    logger.info("📋 Configuration options:")
    logger.info(f"   • Adapter Service URL: {Config.get_adapter_url()}")
    logger.info(f"   • Extract Endpoint: {Config.get_extract_endpoint()}")
    logger.info(f"   • Project ID: {Config.PROJECT_ID}")  
    logger.info(f"   • Storage Bucket: {Config.STORAGE_BUCKET_NAME}")
    logger.info(f"   • Max Batch Size: {Config.MAX_BATCH_SIZE}")
    logger.info(f"   • Environment: {'Production' if Config.is_production() else 'Development'}")
    
    logger.info("\n🔧 To configure, set these environment variables:")
    logger.info("   export ADAPTER_SERVICE_URL='https://your-adapter-service.run.app'")
    logger.info("   export GOOGLE_CLOUD_PROJECT='your-project-id'")
    logger.info("   export STORAGE_BUCKET_NAME='your-bucket-name'")
    logger.info("   export MAX_BATCH_SIZE='25'")
    logger.info("   export ENVIRONMENT='production'")

if __name__ == '__main__':
    logger.info("🎯 Email Batch Processing System - Example Usage")
    logger.info("=" * 60)
    
    # Show configuration
    demonstrate_configuration()
    
    logger.info("\n" + "=" * 60)
    
    # Run the example (commented out to avoid accidental execution)
    # main()
    
    logger.info("✅ Example script completed. Uncomment main() to run actual processing.") 