from google.cloud import firestore
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class FirestoreService:
    def __init__(self):
        """
        Initialize Firestore client
        """
        # Hardcoded values for testing
        self.project_id = "rhea-461313"  
        
        # Initialize Firestore client
        self.db = firestore.Client(project=self.project_id)
        
        # Collection names
        self.emails_collection = "emails"
        self.files_subcollection = "files"
        self.extraction_results_collection = "extraction_results"
        self.calendar_events_collection = "calendar_events"
    
    def get_emails_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Get all documents from the emails collection that match the specified status
        along with their files subcollection
        """
        emails_data = []
        
        try:
            # Query emails by status
            emails_ref = self.db.collection(self.emails_collection)
            emails_query = emails_ref.where("status", "==", status)
            emails = emails_query.stream()
            
            for email in emails:
                email_data = email.to_dict()
                email_data['id'] = email.id
                
                # Get files subcollection for this email
                files_data = self.get_email_files(email.id)
                email_data['files'] = files_data
                
                emails_data.append(email_data)
                
        except Exception as e:
            print(f"Error fetching emails with status '{status}': {e}")
            raise e
        
        return emails_data
    
    def get_email_files(self, email_id: str) -> List[Dict[str, Any]]:
        """
        Get all files from the files subcollection of a specific email
        """
        files_data = []
        
        try:
            # Get files subcollection
            files_ref = self.db.collection(self.emails_collection).document(email_id).collection(self.files_subcollection)
            files = files_ref.stream()
            
            for file_doc in files:
                file_data = file_doc.to_dict()
                file_data['id'] = file_doc.id
                files_data.append(file_data)
                
        except Exception as e:
            print(f"Error fetching files for email {email_id}: {e}")
            raise e
        
        return files_data
    
    def test_connection(self) -> bool:
        """
        Test the Firestore connection
        """
        try:
            # Try to read a small amount of data to test connection
            collections = list(self.db.collections())
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def update_email_status(self, email_id: str, new_status: str) -> bool:
        """
        Update the status of an email
        """
        try:
            email_ref = self.db.collection(self.emails_collection).document(email_id)
            email_ref.update({
                "status": new_status,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
            
            logger.info(f"Updated email {email_id} status to: {new_status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating email status: {e}")
            return False
    
    def update_file_extraction_status(self, email_id: str, file_id: str, new_status: str) -> bool:
        """
        Update the extraction status of a file
        """
        try:
            file_ref = self.db.collection(self.emails_collection).document(email_id).collection(self.files_subcollection).document(file_id)
            file_ref.update({
                "extraction_status": new_status,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
            
            logger.info(f"Updated file {file_id} extraction status to: {new_status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating file extraction status: {e}")
            return False
    
    def save_extraction_result(self, email_id: str, extraction_data: Dict[str, Any]) -> bool:
        """
        Save extraction results for an email
        
        Args:
            email_id: The email ID
            extraction_data: Extracted data from the adapter service
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Save extraction result
            extraction_ref = self.db.collection(self.extraction_results_collection).document(email_id)
            extraction_ref.set({
                "email_id": email_id,
                "summary": extraction_data.get("Summary", ""),
                "action_items": extraction_data.get("ActionItems", []),
                "urgency": extraction_data.get("Urgency", ""),
                "files": extraction_data.get("files", {}),
                "extracted_at": firestore.SERVER_TIMESTAMP,
                "created_at": firestore.SERVER_TIMESTAMP
            })
            
            logger.info(f"Saved extraction result for email {email_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving extraction result for email {email_id}: {e}")
            return False
    
    def save_calendar_events(self, calendar_events: List[Dict[str, Any]]) -> bool:
        """
        Save calendar events from extraction results
        
        Args:
            calendar_events: List of calendar events to save
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            batch = self.db.batch()
            
            for event in calendar_events:
                # Generate a unique ID for the calendar event
                event_ref = self.db.collection(self.calendar_events_collection).document()
                
                event_data = {
                    "date": event.get("date", ""),
                    "time": event.get("time", ""),
                    "action": event.get("action", ""),
                    "source_mail_id": event.get("source_mail_id", ""),
                    "source_file_id": event.get("source_file_id", ""),
                    "execution_details": event.get("execution_details", {}),
                    "created_at": firestore.SERVER_TIMESTAMP
                }
                
                batch.set(event_ref, event_data)
            
            # Commit all calendar events in a batch
            batch.commit()
            
            logger.info(f"Saved {len(calendar_events)} calendar events")
            return True
            
        except Exception as e:
            logger.error(f"Error saving calendar events: {e}")
            return False
    
    def update_file_gcs_url(self, email_id: str, file_id: str, gcs_url: str) -> bool:
        """
        Update the GCS URL for a file attachment
        
        Args:
            email_id: The email ID
            file_id: The file ID
            gcs_url: The GCS URL where the file is stored
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_ref = self.db.collection(self.emails_collection).document(email_id).collection(self.files_subcollection).document(file_id)
            file_ref.update({
                "cloud_storage_url": gcs_url,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
            
            logger.info(f"Updated GCS URL for file {file_id} in email {email_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating GCS URL for file {file_id}: {e}")
            return False 