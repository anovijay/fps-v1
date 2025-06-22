from google.cloud import storage
import json
import logging
from typing import Dict, Any, Optional
import uuid
import os

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self, bucket_name: str = "rhea_incoming_emails"):
        """
        Initialize Google Cloud Storage client
        """
        self.project_id = "rhea-461313"
        self.bucket_name = bucket_name
        
        # Initialize Storage client
        self.client = storage.Client(project=self.project_id)
        self.bucket = self.client.bucket(self.bucket_name)
    
    def upload_json_data(self, data: Dict[str, Any], folder_name: str, file_name: str) -> bool:
        """
        Upload JSON data to Google Cloud Storage
        
        Args:
            data: Dictionary data to upload as JSON
            folder_name: Folder name in the bucket (e.g., 'firestore_data')
            file_name: File name (e.g., 'mail_register.json')
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create the full path
            blob_path = f"{folder_name}/{file_name}"
            
            # Create blob object
            blob = self.bucket.blob(blob_path)
            
            # Convert data to JSON string
            json_string = json.dumps(data, indent=2, ensure_ascii=False, default=str)
            
            # Upload the JSON data
            blob.upload_from_string(
                json_string,
                content_type='application/json'
            )
            
            logger.info(f"Successfully uploaded {blob_path} to bucket {self.bucket_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading to Google Cloud Storage: {e}")
            return False
    
    def upload_attachment(self, file_content: bytes, file_name: str, email_id: str, file_id: str) -> Optional[str]:
        """
        Upload attachment file to Google Cloud Storage and return the public URL
        
        Args:
            file_content: File content as bytes
            file_name: Original file name
            email_id: Email ID for organizing files
            file_id: Unique file ID
        
        Returns:
            str: GCS URL if successful, None otherwise
        """
        try:
            # Create organized path: attachments/email_id/file_id_filename
            safe_file_name = self._sanitize_filename(file_name)
            blob_path = f"attachments/{email_id}/{file_id}_{safe_file_name}"
            
            # Create blob object
            blob = self.bucket.blob(blob_path)
            
            # Upload the file content
            blob.upload_from_string(file_content)
            
            # Generate public URL
            gcs_url = f"gs://{self.bucket_name}/{blob_path}"
            
            logger.info(f"Successfully uploaded attachment {file_name} to {gcs_url}")
            return gcs_url
            
        except Exception as e:
            logger.error(f"Error uploading attachment {file_name}: {e}")
            return None
    
    def upload_attachment_from_path(self, file_path: str, file_name: str, email_id: str, file_id: str) -> Optional[str]:
        """
        Upload attachment file from local path to Google Cloud Storage
        
        Args:
            file_path: Local file path
            file_name: Original file name
            email_id: Email ID for organizing files
            file_id: Unique file ID
        
        Returns:
            str: GCS URL if successful, None otherwise
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            return self.upload_attachment(file_content, file_name, email_id, file_id)
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for GCS storage
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename
    
    def test_connection(self) -> bool:
        """
        Test the Google Cloud Storage connection
        """
        try:
            # Try to access the bucket to test connection
            bucket = self.client.get_bucket(self.bucket_name)
            logger.info(f"Successfully connected to bucket: {bucket.name}")
            return True
        except Exception as e:
            logger.error(f"Storage connection test failed: {e}")
            return False 