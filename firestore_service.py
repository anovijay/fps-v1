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
        self.file_extraction_results_collection = "file_extraction_results"  # NEW: Structured file results
        self.calendar_events_collection = "calendar_events"
        self.finance_events_collection = "finance_events"  # NEW: Finance events collection
    
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
        Save extraction results with structured file data for easy querying by other services
        
        Args:
            email_id: The email ID
            extraction_data: Extracted data from the adapter service
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Use a batch for atomic operations
            batch = self.db.batch()
            
            # 1. Save main email extraction result (keep backward compatibility)
            extraction_ref = self.db.collection(self.extraction_results_collection).document(email_id)
            email_data = {
                "email_id": email_id,
                "summary": extraction_data.get("Summary", ""),
                "action_items": extraction_data.get("ActionItems", []),
                "urgency": extraction_data.get("Urgency", ""),
                "has_files": bool(extraction_data.get("files", {})),
                "files_count": len(extraction_data.get("files", {})),
                "files": extraction_data.get("files", {}),  # Keep for backward compatibility
                "extracted_at": firestore.SERVER_TIMESTAMP,
                "created_at": firestore.SERVER_TIMESTAMP
            }
            batch.set(extraction_ref, email_data)
            
            # 2. Save each file as a separate document for easy querying by other services
            files_data = extraction_data.get("files", {})
            
            # Handle case where files might be empty but extraction data contains nested structure
            if not files_data:
                # Try to find files in nested structure (for backward compatibility with existing data)
                for key, value in extraction_data.items():
                    if isinstance(value, dict) and 'files' in value and value['files']:
                        files_data = value['files']
                        logger.info(f"Found files in nested structure under key '{key}' for email {email_id}")
                        break
            
            if files_data:
                for file_id, file_result in files_data.items():
                    file_doc_id = f"{email_id}_{file_id}"
                    file_extraction_ref = self.db.collection(self.file_extraction_results_collection).document(file_doc_id)
                    
                    # Structure file data for easy querying by other services
                    file_doc = {
                        # Reference fields
                        "email_id": email_id,
                        "file_id": file_id,
                        
                        # Core extraction fields
                        "document_type": file_result.get("Type", ""),
                        "sender": file_result.get("sender", ""),
                        "received_date": file_result.get("received_date", ""),
                        "summary": file_result.get("Summary", ""),
                        "details": file_result.get("Details", ""),
                        "tags": file_result.get("tags", []),
                        "urgency": file_result.get("Urgency", ""),
                        
                        # Financial fields (for expense tracking services)
                        "payment_status": file_result.get("Status", "Unknown"),
                        "action_required": file_result.get("ActionRequired", ""),
                        "amount": file_result.get("Amount", ""),
                        
                        # Payment details (flattened for easy querying)
                        "payment_due_date": "",
                        "payment_method": "",
                        "payment_reference": "",
                        "payment_recipient": "",
                        
                        # Document categorization (for daily briefings)
                        "is_invoice": file_result.get("Type", "").lower() == "invoice",
                        "is_receipt": file_result.get("Type", "").lower() == "receipt",
                        "is_contract": file_result.get("Type", "").lower() == "contract",
                        "is_bill": file_result.get("Type", "").lower() in ["bill", "utility bill", "phone bill"],
                        
                        # Additional fields
                        "authority": file_result.get("Authority", ""),
                        "reference": file_result.get("Reference", ""),
                        "location": file_result.get("Location", ""),
                        
                        # Timestamps
                        "extracted_at": firestore.SERVER_TIMESTAMP,
                        "created_at": firestore.SERVER_TIMESTAMP,
                        
                        # Keep original data for backward compatibility
                        "original_data": file_result
                    }
                    
                    # Parse payment details if available
                    payment_details = file_result.get("PaymentDetails", {})
                    if payment_details:
                        file_doc["payment_due_date"] = payment_details.get("due_date", "")
                        file_doc["payment_method"] = payment_details.get("method", "")
                        file_doc["payment_reference"] = payment_details.get("reference", "")
                        file_doc["payment_recipient"] = payment_details.get("recipient", "")
                    
                    batch.set(file_extraction_ref, file_doc)
            
            # Commit all operations atomically
            batch.commit()
            
            # 3. Handle calendar events if present in extraction data
            calendar_events = extraction_data.get("calendar_add_details", [])
            if calendar_events and isinstance(calendar_events, list):
                try:
                    self.save_calendar_events(calendar_events)
                    logger.info(f"Saved {len(calendar_events)} calendar events for email {email_id}")
                except Exception as e:
                    logger.error(f"Failed to save calendar events for email {email_id}: {e}")
            
            # 4. Handle finance events if present in extraction data
            finance_events = extraction_data.get("finance_events", [])
            if finance_events and isinstance(finance_events, list):
                try:
                    self.save_finance_events(finance_events)
                    logger.info(f"Saved {len(finance_events)} finance events for email {email_id}")
                except Exception as e:
                    logger.error(f"Failed to save finance events for email {email_id}: {e}")
            
            logger.info(f"Saved extraction result for email {email_id} with {len(files_data)} file results")
            return True
            
        except Exception as e:
            logger.error(f"Error saving extraction result for email {email_id}: {e}")
            return False
    
    # NEW METHODS FOR OTHER SERVICES TO QUERY STRUCTURED DATA
    
    def get_unpaid_invoices(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all unpaid invoices for expense tracking services
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of unpaid invoice documents
        """
        try:
            query = self.db.collection(self.file_extraction_results_collection)\
                          .where("is_invoice", "==", True)\
                          .where("payment_status", "==", "Unpaid")\
                          .order_by("received_date", direction=firestore.Query.DESCENDING)\
                          .limit(limit)
            
            results = []
            for doc in query.stream():
                result = doc.to_dict()
                result['id'] = doc.id
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching unpaid invoices: {e}")
            return []
    
    def get_monthly_expenses(self, year: int, month: int) -> List[Dict[str, Any]]:
        """
        Get all expenses for a specific month for monthly expense reports
        
        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
            
        Returns:
            List of expense documents for the month
        """
        try:
            # Format dates for querying
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year + 1}-01-01"
            else:
                end_date = f"{year}-{month + 1:02d}-01"
            
            query = self.db.collection(self.file_extraction_results_collection)\
                          .where("is_invoice", "==", True)\
                          .where("received_date", ">=", start_date)\
                          .where("received_date", "<", end_date)\
                          .order_by("received_date")
            
            results = []
            for doc in query.stream():
                result = doc.to_dict()
                result['id'] = doc.id
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching monthly expenses for {year}-{month:02d}: {e}")
            return []
    
    def get_urgent_items_for_briefing(self, urgency_levels: List[str] = ["High", "Critical"]) -> List[Dict[str, Any]]:
        """
        Get all urgent items for daily briefings
        
        Args:
            urgency_levels: List of urgency levels to include
            
        Returns:
            List of urgent documents
        """
        try:
            query = self.db.collection(self.file_extraction_results_collection)\
                          .where("urgency", "in", urgency_levels)\
                          .order_by("received_date", direction=firestore.Query.DESCENDING)
            
            results = []
            for doc in query.stream():
                result = doc.to_dict()
                result['id'] = doc.id
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching urgent items: {e}")
            return []
    
    def get_documents_by_type(self, document_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all documents of a specific type
        
        Args:
            document_type: Type of document (e.g., "Invoice", "Receipt", "Contract")
            limit: Maximum number of results to return
            
        Returns:
            List of documents of the specified type
        """
        try:
            query = self.db.collection(self.file_extraction_results_collection)\
                          .where("document_type", "==", document_type)\
                          .order_by("received_date", direction=firestore.Query.DESCENDING)\
                          .limit(limit)
            
            results = []
            for doc in query.stream():
                result = doc.to_dict()
                result['id'] = doc.id
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching documents of type {document_type}: {e}")
            return []
    
    def get_payment_due_soon(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get invoices with payments due within specified days
        
        Args:
            days_ahead: Number of days ahead to check for due payments
            
        Returns:
            List of invoices with upcoming due dates
        """
        try:
            from datetime import datetime, timedelta
            
            today = datetime.now().strftime("%Y-%m-%d")
            future_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
            
            query = self.db.collection(self.file_extraction_results_collection)\
                          .where("is_invoice", "==", True)\
                          .where("payment_status", "==", "Unpaid")\
                          .where("payment_due_date", ">=", today)\
                          .where("payment_due_date", "<=", future_date)\
                          .order_by("payment_due_date")
            
            results = []
            for doc in query.stream():
                result = doc.to_dict()
                result['id'] = doc.id
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching payments due soon: {e}")
            return []

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

    def save_finance_events(self, finance_events: List[Dict[str, Any]]) -> bool:
        """
        Save finance events from extraction results
        
        Args:
            finance_events: List of finance events to save
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            batch = self.db.batch()
            
            for event in finance_events:
                # Generate a unique ID for the finance event
                event_ref = self.db.collection(self.finance_events_collection).document()
                
                event_data = {
                    "type": event.get("type", ""),  # Expense, Income, Transfer, etc.
                    "amount": event.get("amount", ""),
                    "currency": event.get("currency", ""),
                    "date": event.get("date", ""),
                    "category": event.get("category", ""),
                    "payee": event.get("payee", ""),
                    "source_mail_id": event.get("source_mail_id", ""),
                    "source_file_id": event.get("source_file_id", ""),
                    "created_at": firestore.SERVER_TIMESTAMP
                }
                
                batch.set(event_ref, event_data)
            
            # Commit all finance events in a batch
            batch.commit()
            
            logger.info(f"Saved {len(finance_events)} finance events")
            return True
            
        except Exception as e:
            logger.error(f"Error saving finance events: {e}")
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