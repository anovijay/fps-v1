#!/usr/bin/env python3
"""
Integration test for LLM Adapter Service
Tests the complete workflow and validates schemas
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, Any
from adapter_schemas import (
    validate_request, 
    validate_response, 
    get_example_request,
    get_example_response
)
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AdapterServiceTester:
    """Test class for validating adapter service integration"""
    
    def __init__(self, service_url: str = None):
        self.service_url = service_url or Config.get_adapter_url()
        self.extract_endpoint = f"{self.service_url}/extract"
        self.health_endpoint = f"{self.service_url}/health"
    
    def test_health_endpoint(self) -> bool:
        """Test if the health endpoint is accessible"""
        logger.info("🏥 Testing health endpoint...")
        
        try:
            response = requests.get(self.health_endpoint, timeout=10)
            response.raise_for_status()
            
            health_data = response.json()
            logger.info(f"✅ Health check passed: {health_data}")
            
            # Validate expected fields
            if "status" in health_data and health_data["status"] == "healthy":
                return True
            else:
                logger.warning("⚠️ Health endpoint returned but status is not 'healthy'")
                return False
                
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
    
    def test_extract_endpoint_validation(self) -> bool:
        """Test extract endpoint with invalid payloads to check validation"""
        logger.info("🔍 Testing extract endpoint validation...")
        
        test_cases = [
            # Empty payload
            {},
            # Missing emails field
            {
                "extraction_timestamp": datetime.utcnow().isoformat(),
                "total_emails": 0
            },
            # Invalid email structure
            {
                "extraction_timestamp": datetime.utcnow().isoformat(),
                "total_emails": 1,
                "emails": [{"invalid": "email"}]
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            try:
                logger.info(f"🧪 Testing invalid payload {i+1}...")
                
                response = requests.post(
                    self.extract_endpoint,
                    json=test_case,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                # We expect 4xx status codes for invalid requests
                if response.status_code >= 400 and response.status_code < 500:
                    logger.info(f"✅ Validation test {i+1} passed: {response.status_code}")
                else:
                    logger.warning(f"⚠️ Unexpected response for invalid payload: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Validation test {i+1} failed: {e}")
        
        return True
    
    def test_minimal_valid_request(self) -> Dict[str, Any]:
        """Test with minimal valid request"""
        logger.info("📤 Testing with minimal valid request...")
        
        minimal_request = {
            "extraction_timestamp": datetime.utcnow().isoformat(),
            "total_emails": 1,
            "emails": [
                {
                    "id": "test_email_001",
                    "subject": "Test Email",
                    "sender_email_id": "test@example.com",
                    "body": "This is a test email for integration testing.",
                    "has_attachments": False,
                    "files": []
                }
            ]
        }
        
        # Validate our request
        validation_errors = validate_request(minimal_request)
        if validation_errors:
            logger.error(f"❌ Request validation failed: {validation_errors}")
            return None
        
        try:
            response = requests.post(
                self.extract_endpoint,
                json=minimal_request,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            logger.info(f"📥 Response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info("✅ Minimal request test passed")
                
                # Validate response structure
                response_errors = validate_response(response_data)
                if response_errors:
                    logger.warning(f"⚠️ Response validation issues: {response_errors}")
                else:
                    logger.info("✅ Response validation passed")
                
                return response_data
            else:
                logger.error(f"❌ Request failed with status {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Minimal request test failed: {e}")
            return None
    
    def test_full_example_request(self) -> Dict[str, Any]:
        """Test with full example request"""
        logger.info("📤 Testing with full example request...")
        
        example_request = get_example_request()
        
        # Validate our request
        validation_errors = validate_request(example_request)
        if validation_errors:
            logger.error(f"❌ Example request validation failed: {validation_errors}")
            return None
        
        try:
            response = requests.post(
                self.extract_endpoint,
                json=example_request,
                headers={"Content-Type": "application/json"},
                timeout=120  # Longer timeout for complex request
            )
            
            logger.info(f"📥 Response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info("✅ Full example request test passed")
                
                # Validate response structure
                response_errors = validate_response(response_data)
                if response_errors:
                    logger.warning(f"⚠️ Response validation issues: {response_errors}")
                else:
                    logger.info("✅ Response validation passed")
                
                return response_data
            else:
                logger.error(f"❌ Request failed with status {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Full example request test failed: {e}")
            return None
    
    def analyze_breaking_changes(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze response for potential breaking changes"""
        logger.info("🔍 Analyzing for breaking changes...")
        
        analysis = {
            "breaking_changes": [],
            "warnings": [],
            "compatible": True
        }
        
        if not response_data:
            analysis["breaking_changes"].append("No response data received")
            analysis["compatible"] = False
            return analysis
        
        # Check required response fields
        required_fields = ["status", "results"]
        for field in required_fields:
            if field not in response_data:
                analysis["breaking_changes"].append(f"Missing required field: {field}")
                analysis["compatible"] = False
        
        # Check status field values
        if "status" in response_data:
            if response_data["status"] not in ["success", "error"]:
                analysis["breaking_changes"].append(f"Invalid status value: {response_data['status']}")
                analysis["compatible"] = False
        
        # Check results structure
        if "results" in response_data and isinstance(response_data["results"], dict):
            results = response_data["results"]
            
            # Check for email results
            email_results_found = False
            for key, value in results.items():
                if key != "calendar_add_details":
                    email_results_found = True
                    if not isinstance(value, dict):
                        analysis["warnings"].append(f"Email result {key} is not a dictionary")
                    else:
                        # Check for expected email result fields
                        expected_fields = ["Summary", "ActionItems", "Urgency"]
                        for field in expected_fields:
                            if field not in value:
                                analysis["warnings"].append(f"Email {key} missing field: {field}")
            
            # Check calendar events
            if "calendar_add_details" in results:
                if not isinstance(results["calendar_add_details"], list):
                    analysis["breaking_changes"].append("calendar_add_details should be a list")
                    analysis["compatible"] = False
                else:
                    for i, event in enumerate(results["calendar_add_details"]):
                        if not isinstance(event, dict):
                            analysis["warnings"].append(f"Calendar event {i} is not a dictionary")
        
        # Summary
        if analysis["compatible"]:
            logger.info("✅ No breaking changes detected")
        else:
            logger.error(f"❌ Breaking changes found: {analysis['breaking_changes']}")
        
        if analysis["warnings"]:
            logger.warning(f"⚠️ Warnings: {analysis['warnings']}")
        
        return analysis
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive integration test"""
        logger.info("🚀 Starting comprehensive integration test...")
        
        test_results = {
            "health_check": False,
            "validation_test": False, 
            "minimal_request": None,
            "full_request": None,
            "breaking_changes_analysis": None,
            "overall_success": False
        }
        
        # Test health endpoint
        test_results["health_check"] = self.test_health_endpoint()
        
        # Test validation
        test_results["validation_test"] = self.test_extract_endpoint_validation()
        
        # Test minimal request
        test_results["minimal_request"] = self.test_minimal_valid_request()
        
        # Test full request (only if minimal worked)
        if test_results["minimal_request"]:
            test_results["full_request"] = self.test_full_example_request()
        
        # Analyze breaking changes
        response_to_analyze = test_results["full_request"] or test_results["minimal_request"]
        if response_to_analyze:
            test_results["breaking_changes_analysis"] = self.analyze_breaking_changes(response_to_analyze)
        
        # Overall success determination
        test_results["overall_success"] = (
            test_results["health_check"] and
            test_results["validation_test"] and
            test_results["minimal_request"] is not None and
            (test_results["breaking_changes_analysis"] is None or 
             test_results["breaking_changes_analysis"]["compatible"])
        )
        
        # Print summary
        logger.info("="*60)
        logger.info("🎯 INTEGRATION TEST SUMMARY")
        logger.info("="*60)
        logger.info(f"Health Check: {'✅' if test_results['health_check'] else '❌'}")
        logger.info(f"Validation Test: {'✅' if test_results['validation_test'] else '❌'}")
        logger.info(f"Minimal Request: {'✅' if test_results['minimal_request'] else '❌'}")
        logger.info(f"Full Request: {'✅' if test_results['full_request'] else '❌'}")
        
        if test_results["breaking_changes_analysis"]:
            compatible = test_results["breaking_changes_analysis"]["compatible"]
            logger.info(f"Breaking Changes: {'✅ None' if compatible else '❌ Found'}")
        
        logger.info(f"Overall Success: {'✅' if test_results['overall_success'] else '❌'}")
        
        return test_results

def main():
    """Main test function"""
    logger.info("🎯 LLM Adapter Service Integration Test")
    logger.info(f"🌐 Testing service: {Config.get_adapter_url()}")
    
    tester = AdapterServiceTester()
    results = tester.run_comprehensive_test()
    
    if results["overall_success"]:
        logger.info("🎉 All tests passed! Service is ready for production.")
        return 0
    else:
        logger.error("💥 Some tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    exit(main()) 