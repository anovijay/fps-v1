#!/usr/bin/env python3
"""
Email Data Batch Processor - Enhanced Version
Fetches emails from Firestore, uploads attachments to GCS, calls adapter service for extraction,
and saves results back to Firestore with enhanced error handling and transaction-like behavior
"""

import os
import json
import logging
import sys
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from firestore_service import FirestoreService
from storage_service import StorageService
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BatchProcessor:
    def __init__(self, adapter_service_url: str = None):
        """
        Initialize the batch processor
        
        Args:
            adapter_service_url: URL of the adapter service (e.g., 'https://llm-adapter-service-url.run.app')
        """
        self.firestore_service = FirestoreService()
        self.storage_service = StorageService()
        self.adapter_service_url = adapter_service_url or Config.get_adapter_url()
        
    def collect_email_batch_with_attachments(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Step 1: Collect email batch and process attachments
        
        Args:
            emails: Raw email data from Firestore
            
        Returns:
            List of emails with attachment info and GCS URLs
        """
        logger.info("📦 Processing email batch with attachments...")
        processed_emails = []
        
        for email in emails:
            try:
                email_id = email['id']
                
                # Build base email structure with enhanced fields per API documentation
                processed_email = {
                    "id": email_id,
                    "subject": email.get('subject', ''),
                    "sender_email_id": email.get('sender_email_id', email.get('from', '')),
                    "body": email.get('body', ''),
                    "has_attachments": len(email.get('files', [])) > 0,
                    "files": []
                }
                
                # Add updated_at field if available (API documentation optional field)
                if 'updated_at' in email and email['updated_at']:
                    # Convert Firestore timestamp to ISO format if needed
                    updated_at = email['updated_at']
                    if hasattr(updated_at, 'isoformat'):
                        processed_email["updated_at"] = updated_at.isoformat()
                    else:
                        processed_email["updated_at"] = str(updated_at)
                
                # Process attachments
                if email.get('files'):
                    for file_data in email['files']:
                        file_id = file_data['id']
                        file_name = file_data.get('file_name', f'attachment_{file_id}')
                        
                        # Upload attachment to GCS if it has content
                        gcs_url = None
                        if 'file_path' in file_data and file_data['file_path']:
                            # Upload from local file path
                            gcs_url = self.storage_service.upload_attachment_from_path(
                                file_data['file_path'], 
                                file_name, 
                                email_id, 
                                file_id
                            )
                        elif 'file_content' in file_data and file_data['file_content']:
                            # Upload from file content (bytes)
                            gcs_url = self.storage_service.upload_attachment(
                                file_data['file_content'], 
                                file_name, 
                                email_id, 
                                file_id
                            )
                        
                        # If upload successful, update Firestore with GCS URL
                        if gcs_url:
                            self.firestore_service.update_file_gcs_url(email_id, file_id, gcs_url)
                        else:
                            # Use existing cloud_storage_url if available
                            gcs_url = file_data.get('cloud_storage_url', '')
                        
                        # Add file info to processed email
                        processed_email["files"].append({
                            "id": file_id,
                            "file_name": file_name,
                            "cloud_storage_url": gcs_url
                        })
                
                processed_emails.append(processed_email)
                logger.info(f"✅ Processed email {email_id} with {len(processed_email['files'])} attachments")
                
            except Exception as e:
                logger.error(f"❌ Error processing email {email.get('id', 'unknown')}: {e}")
                continue
        
        return processed_emails
    
    def build_adapter_payload(self, email_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Step 2: Build the adapter payload with the required schema
        
        Args:
            email_batch: Processed email batch with attachment info
            
        Returns:
            Adapter payload dictionary
        """
        logger.info("🔧 Building adapter payload...")
        
        adapter_payload = {
            "extraction_timestamp": datetime.utcnow().isoformat(),
            "total_emails": len(email_batch),
            "emails": email_batch
        }
        
        logger.info(f"📋 Built payload with {len(email_batch)} emails")
        return adapter_payload
    
    def call_adapter_service(self, adapter_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Step 3: POST to Adapter /extract Endpoint
        
        Args:
            adapter_payload: The payload to send to the adapter service
            
        Returns:
            Response from adapter service or None if failed
        """
        logger.info("🌐 Calling adapter service...")
        
        try:
            url = f"{self.adapter_service_url}/extract"
            headers = {"Content-Type": "application/json"}
            
            logger.info(f"📤 Sending request to {url}")
            
            response = requests.post(
                url, 
                json=adapter_payload, 
                headers=headers,
                timeout=300  # 5 minute timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("✅ Adapter service call successful")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Adapter service call failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse adapter service response: {e}")
            return None

    def extract_email_data_with_resilience(self, email_id: str, email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Enhanced data extraction with multiple fallback strategies for different response formats
        
        Args:
            email_id: The email ID
            email_data: Raw email data from adapter response
            
        Returns:
            Extracted email data or None if extraction fails
        """
        try:
            # Strategy 1: Check for MAIL_1 wrapper (current known format)
            if "MAIL_1" in email_data:
                logger.info(f"📧 Found MAIL_1 wrapper for email {email_id}")
                return email_data["MAIL_1"]
            
            # Strategy 2: Check for other common wrapper patterns
            for potential_wrapper in ["MAIL_0", "EMAIL_1", "EMAIL_0", "data", "content"]:
                if potential_wrapper in email_data:
                    logger.info(f"📧 Found {potential_wrapper} wrapper for email {email_id}")
                    return email_data[potential_wrapper]
            
            # Strategy 3: Check if data has expected fields directly (no wrapper)
            expected_fields = ["Summary", "ActionItems", "Urgency", "files"]
            if any(field in email_data for field in expected_fields):
                logger.info(f"📧 Using direct structure for email {email_id}")
                return email_data
            
            # Strategy 4: Check if it's a list and take first element
            if isinstance(email_data, list) and len(email_data) > 0:
                logger.info(f"📧 Found list format for email {email_id}, taking first element")
                return email_data[0]
            
            # Strategy 5: Last resort - return as-is and let downstream handle it
            logger.warning(f"⚠️ Unknown format for email {email_id}, returning as-is")
            return email_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting data for email {email_id}: {e}")
            return None

    def validate_extraction_data(self, email_id: str, extraction_data: Dict[str, Any]) -> bool:
        """
        Validate that extraction data matches API documentation requirements
        Enhanced to check for required fields per API specification
        
        Args:
            email_id: The email ID
            extraction_data: Extracted data to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Check for required fields as per API documentation
            required_fields = ["Summary", "ActionItems", "Urgency"]
            for field in required_fields:
                if field not in extraction_data:
                    logger.warning(f"⚠️ Email {email_id} missing required field: {field}")
                    return False
            
            # Validate field types
            if not isinstance(extraction_data.get("ActionItems", []), list):
                logger.warning(f"⚠️ Email {email_id} ActionItems must be a list")
                return False
            
            # Validate Urgency value
            valid_urgency = ["Low", "Medium", "High", "Critical"]
            if extraction_data.get("Urgency") not in valid_urgency:
                logger.warning(f"⚠️ Email {email_id} invalid Urgency value: {extraction_data.get('Urgency')}")
                return False
            
            # Validate files structure if present
            if "files" in extraction_data and extraction_data["files"]:
                if not isinstance(extraction_data["files"], dict):
                    logger.warning(f"⚠️ Email {email_id} files must be a dictionary")
                    return False
                
                # Validate each file result
                for file_id, file_result in extraction_data["files"].items():
                    if not self.validate_file_extraction_result(email_id, file_id, file_result):
                        return False
            
            logger.debug(f"✅ Email {email_id} extraction data validation passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error validating extraction data for email {email_id}: {e}")
            return False
    
    def validate_file_extraction_result(self, email_id: str, file_id: str, file_result: Dict[str, Any]) -> bool:
        """
        Validate file extraction result against API documentation requirements
        
        Args:
            email_id: The email ID
            file_id: The file ID
            file_result: File extraction result to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields for file results as per API documentation
            required_fields = ["Type", "sender", "received_date", "Summary", "Details", "tags", "Urgency"]
            for field in required_fields:
                if field not in file_result:
                    logger.warning(f"⚠️ File {file_id} in email {email_id} missing required field: {field}")
                    return False
            
            # Validate tags is a list
            if not isinstance(file_result.get("tags", []), list):
                logger.warning(f"⚠️ File {file_id} in email {email_id} tags must be a list")
                return False
            
            # Validate Status if present (optional field)
            if "Status" in file_result:
                valid_status = ["Paid", "Unpaid", "Unknown"]
                if file_result["Status"] not in valid_status:
                    logger.warning(f"⚠️ File {file_id} in email {email_id} invalid Status: {file_result['Status']}")
                    return False
            
            # Validate Urgency value
            valid_urgency = ["Low", "Medium", "High", "Critical"]
            if file_result.get("Urgency") not in valid_urgency:
                logger.warning(f"⚠️ File {file_id} in email {email_id} invalid Urgency: {file_result.get('Urgency')}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error validating file result {file_id} for email {email_id}: {e}")
            return False
    
    def validate_calendar_event(self, event: Dict[str, Any], event_reference: str) -> bool:
        """
        Validate calendar event structure against API documentation requirements
        
        Args:
            event: Calendar event to validate
            event_reference: Reference string for logging
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields for calendar events as per API documentation
            required_fields = ["date", "time", "action", "source_mail_id"]
            for field in required_fields:
                if field not in event:
                    logger.warning(f"⚠️ {event_reference} missing required field: {field}")
                    return False
                if not event[field]:  # Check for empty values
                    logger.warning(f"⚠️ {event_reference} field '{field}' cannot be empty")
                    return False
            
            # source_file_id can be null but should be present in the structure
            if "source_file_id" not in event:
                logger.warning(f"⚠️ {event_reference} missing 'source_file_id' field (can be null)")
                return False
            
            logger.debug(f"✅ {event_reference} validation passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error validating calendar event {event_reference}: {e}")
            return False

    def process_single_email_extraction(self, email_id: str, email_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Process extraction data for a single email with enhanced error handling
        
        Args:
            email_id: The email ID
            email_data: Raw email data from adapter response
            
        Returns:
            Tuple of (success: bool, error_message: str)
        """
        try:
            # Step 1: Extract data with resilience strategies
            extraction_data = self.extract_email_data_with_resilience(email_id, email_data)
            if not extraction_data:
                return False, "Failed to extract email data from response"
            
            # Step 2: Validate extraction data
            if not self.validate_extraction_data(email_id, extraction_data):
                return False, "Extraction data validation failed"
            
            # Step 3: Save extraction result to Firestore
            if not self.firestore_service.save_extraction_result(email_id, extraction_data):
                return False, "Failed to save extraction result to Firestore"
            
            # Step 4: Update file statuses if they exist
            if "files" in extraction_data and extraction_data["files"]:
                for file_id in extraction_data["files"].keys():
                    try:
                        self.firestore_service.update_file_extraction_status(
                            email_id, 
                            file_id, 
                            Config.STATUS_EXTRACTED
                        )
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to update file status {file_id} for email {email_id}: {e}")
                        # Don't fail the whole operation for file status updates
            
            logger.info(f"✅ Successfully processed extraction for email {email_id}")
            return True, ""
            
        except Exception as e:
            error_msg = f"Error processing extraction for email {email_id}: {e}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

    def handle_adapter_response(self, adapter_response: Dict[str, Any], processed_email_ids: List[str]) -> Tuple[bool, List[str], List[str]]:
        """
        Step 4: Handle the Adapter Response with Enhanced Error Handling
        
        Args:
            adapter_response: Response from the adapter service
            processed_email_ids: List of email IDs that were sent to adapter
            
        Returns:
            Tuple of (overall_success: bool, successful_email_ids: List[str], failed_email_ids: List[str])
        """
        logger.info("📊 Processing adapter response with enhanced error handling...")
        
        successful_email_ids = []
        failed_email_ids = []
        
        try:
            # Check adapter response status
            if adapter_response.get('status') != 'success':
                error_msg = f"Adapter service returned error status: {adapter_response.get('status')}"
                logger.error(f"❌ {error_msg}")
                return False, [], processed_email_ids
            
            results = adapter_response.get('results', {})
            
            # Process each email extraction result
            for email_id, email_data in results.items():
                # Skip calendar events
                if email_id == "calendar_add_details":
                    continue
                
                # Process single email extraction
                success, error_msg = self.process_single_email_extraction(email_id, email_data)
                
                if success:
                    successful_email_ids.append(email_id)
                else:
                    failed_email_ids.append(email_id)
                    logger.error(f"❌ Failed to process email {email_id}: {error_msg}")
            
            # Process calendar events separately
            calendar_events = results.get("calendar_add_details", [])
            if calendar_events:
                try:
                    # Validate calendar events structure
                    valid_events = []
                    for i, event in enumerate(calendar_events):
                        if self.validate_calendar_event(event, f"calendar_add_details[{i}]"):
                            valid_events.append(event)
                        else:
                            logger.warning(f"⚠️ Skipping invalid calendar event {i}: {event}")
                    
                    if valid_events:
                        self.firestore_service.save_calendar_events(valid_events)
                        logger.info(f"📅 Saved {len(valid_events)} calendar events")
                    else:
                        logger.info("📅 No valid calendar events to save")
                except Exception as e:
                    logger.error(f"❌ Failed to save calendar events: {e}")
                    # Don't fail the whole operation for calendar events
            
            # Log summary
            logger.info(f"📊 Processing summary:")
            logger.info(f"   • Successfully processed: {len(successful_email_ids)} emails")
            logger.info(f"   • Failed to process: {len(failed_email_ids)} emails")
            
            # Overall success if at least one email was processed successfully
            overall_success = len(successful_email_ids) > 0
            
            return overall_success, successful_email_ids, failed_email_ids
            
        except Exception as e:
            logger.error(f"❌ Critical error handling adapter response: {e}")
            return False, [], processed_email_ids

    def update_email_statuses(self, successful_email_ids: List[str], failed_email_ids: List[str]) -> None:
        """
        Update email statuses based on processing results
        CRITICAL: Only update status to 'Extracted' if ALL operations succeeded
        
        Args:
            successful_email_ids: List of email IDs that were successfully processed
            failed_email_ids: List of email IDs that failed processing
        """
        logger.info("🔄 Updating email statuses based on processing results...")
        
        # Update successful emails to 'Extracted' status
        for email_id in successful_email_ids:
            try:
                self.firestore_service.update_email_status(email_id, Config.STATUS_EXTRACTED)
                logger.info(f"✅ Updated email {email_id} status to '{Config.STATUS_EXTRACTED}'")
            except Exception as e:
                logger.error(f"❌ Failed to update status for email {email_id}: {e}")
        
        # Failed emails remain in 'Scheduled for Extraction' status for retry
        if failed_email_ids:
            logger.info(f"⚠️ {len(failed_email_ids)} emails remain in '{Config.STATUS_SCHEDULED_FOR_EXTRACTION}' status for retry:")
            for email_id in failed_email_ids:
                logger.info(f"   • {email_id}")

    def process_batch(self) -> bool:
        """
        Main batch processing function implementing the complete workflow with enhanced error handling
        
        Returns:
            bool: True if at least one email was processed successfully, False if complete failure
        """
        try:
            logger.info("🚀 Starting enhanced email batch processing with adapter integration...")
            
            # Test connections
            logger.info("🔍 Testing service connections...")
            if not self.storage_service.test_connection():
                logger.error("❌ Failed to connect to Google Cloud Storage")
                return False
            
            if not self.firestore_service.test_connection():
                logger.error("❌ Failed to connect to Firestore")
                return False
            
            # Step 1: Get emails scheduled for extraction
            logger.info("📧 Fetching emails scheduled for extraction...")
            emails = self.firestore_service.get_emails_by_status(Config.STATUS_SCHEDULED_FOR_EXTRACTION)
            
            if not emails:
                logger.info(f"✅ No emails found with '{Config.STATUS_SCHEDULED_FOR_EXTRACTION}' status")
                return True
            
            logger.info(f"📦 Found {len(emails)} emails to process")
            
            # Step 2: Collect email batch with attachments
            processed_emails = self.collect_email_batch_with_attachments(emails)
            
            if not processed_emails:
                logger.error("❌ No emails could be processed")
                return False
            
            # Keep track of processed email IDs for status updates
            processed_email_ids = [email['id'] for email in processed_emails]
            
            # Step 3: Build adapter payload
            adapter_payload = self.build_adapter_payload(processed_emails)
            
            # Step 4: Call adapter service
            adapter_response = self.call_adapter_service(adapter_payload)
            
            if not adapter_response:
                logger.error("❌ Failed to get response from adapter service")
                # All emails remain in 'Scheduled for Extraction' status
                return False
            
            # Step 5: Handle adapter response and save results with enhanced error handling
            overall_success, successful_email_ids, failed_email_ids = self.handle_adapter_response(
                adapter_response, processed_email_ids
            )
            
            # Step 6: Update email statuses based on results
            # CRITICAL: Only emails that were successfully processed AND saved get status update
            self.update_email_statuses(successful_email_ids, failed_email_ids)
            
            # Summary logging
            logger.info("🎉 Enhanced batch processing completed!")
            logger.info(f"📊 Final Summary:")
            logger.info(f"   • Total emails found: {len(emails)}")
            logger.info(f"   • Successfully processed: {len(successful_email_ids)}")
            logger.info(f"   • Failed processing: {len(failed_email_ids)}")
            logger.info(f"   • Adapter service: {self.adapter_service_url}")
            logger.info(f"   • Status updated to 'Extracted': {len(successful_email_ids)} emails")
            logger.info(f"   • Remaining for retry: {len(failed_email_ids)} emails")
            
            # Return True if at least one email was processed successfully
            return overall_success
            
        except Exception as e:
            logger.error(f"❌ Critical error in batch processing: {e}", exc_info=True)
            return False

def main():
    """Main function to run the enhanced batch processor"""
    
    # Get adapter service URL from config
    adapter_url = Config.get_adapter_url()
    
    # Initialize and run batch processor
    processor = BatchProcessor(adapter_service_url=adapter_url)
    success = processor.process_batch()
    
    if success:
        logger.info("🎉 Enhanced batch processing completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 Enhanced batch processing failed!")
        sys.exit(1)

if __name__ == '__main__':
    main() 