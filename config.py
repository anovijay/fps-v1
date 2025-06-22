"""
Configuration settings for the FPS (Email Processing Service)
"""

import os

class Config:
    """Configuration class for FPS settings"""
    
    # Adapter Service Configuration
    ADAPTER_SERVICE_URL = os.getenv('ADAPTER_SERVICE_URL', 'https://llm-adapter-317624663818.us-central1.run.app')
    ADAPTER_TIMEOUT_SECONDS = int(os.getenv('ADAPTER_TIMEOUT_SECONDS', '300'))  # 5 minutes
    
    # Google Cloud Configuration
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'rhea-461313')
    STORAGE_BUCKET_NAME = os.getenv('STORAGE_BUCKET_NAME', 'rhea_incoming_emails')
    
    # Firestore Collections
    EMAILS_COLLECTION = 'emails'
    FILES_SUBCOLLECTION = 'files'
    EXTRACTION_RESULTS_COLLECTION = 'extraction_results'
    CALENDAR_EVENTS_COLLECTION = 'calendar_events'
    
    # Processing Configuration
    MAX_BATCH_SIZE = int(os.getenv('MAX_BATCH_SIZE', '50'))  # Max emails per batch
    RETRY_ATTEMPTS = int(os.getenv('RETRY_ATTEMPTS', '3'))
    
    # Status Values
    STATUS_SCHEDULED_FOR_EXTRACTION = "Scheduled for Extraction"
    STATUS_EXTRACTED = "Extracted"
    STATUS_DATA_EXPORTED = "Data Exported"
    STATUS_FAILED = "Failed"
    
    @classmethod
    def get_adapter_url(cls) -> str:
        """Get the full adapter service URL"""
        return cls.ADAPTER_SERVICE_URL
    
    @classmethod 
    def get_extract_endpoint(cls) -> str:
        """Get the full extract endpoint URL"""
        return f"{cls.ADAPTER_SERVICE_URL}/extract"
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return os.getenv('ENVIRONMENT', 'development').lower() == 'production'
    
    @classmethod
    def get_log_level(cls) -> str:
        """Get logging level"""
        return os.getenv('LOG_LEVEL', 'INFO').upper() 