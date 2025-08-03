#!/usr/bin/env python3
"""
Luggixx Backend API Testing Suite
Tests all backend functionality including authentication, ride requests, and role-based access control.
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://4fb3f15c-99ff-43d4-b007-be20c0e24311.preview.emergentagent.com/api"
TIMEOUT = 30

class LuggixxAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        
        # Test data storage
        self.customer_token = None
        self.porter_token = None
        self.customer_user = None
        self.porter_user = None
        self.test_ride_id = None
        
    def log_test(self, test_name: str, success: bool, message: str, details: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=headers)
            else:
                return False, f"Unsupported method: {method}", 0
                
            return True, response.json() if response.content else {}, response.status_code
        except requests.exceptions.RequestException as e:
            return False, str(e), 0
        except json.JSONDecodeError as e:
            return False, f"JSON decode error: {e}", response.status_code if 'response' in locals() else 0
    
    def get_auth_headers(self, token: str) -> Dict[str, str]:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {token}"}
    
    def test_user_registration(self):
        """Test user registration for both customer and porter roles"""
        print("\n=== Testing User Registration ===")
        
        # Test customer registration
        customer_data = {
            "email": "john.doe@example.com",
            "password": "securepass123",
            "name": "John Doe",
            "phone": "+91-9876543220",
            "role": "customer"
        }
        
        success, response, status_code = self.make_request("POST", "/auth/register", customer_data)
        
        if success and status_code == 200:
            if "access_token" in response and "user" in response:
                self.customer_token = response["access_token"]
                self.customer_user = response["user"]
                self.log_test("Customer Registration", True, "Customer registered successfully")
            else:
                self.log_test("Customer Registration", False, "Missing token or user in response", response)
        else:
            self.log_test("Customer Registration", False, f"Registration failed (Status: {status_code})", response)
        
        # Test porter registration
        porter_data = {
            "email": "porter.new@luggixx.com",
            "password": "porterpass123",
            "name": "New Porter",
            "phone": "+91-9876543221",
            "role": "porter"
        }
        
        success, response, status_code = self.make_request("POST", "/auth/register", porter_data)
        
        if success and status_code == 200:
            if "access_token" in response and "user" in response:
                self.porter_token = response["access_token"]
                self.porter_user = response["user"]
                self.log_test("Porter Registration", True, "Porter registered successfully")
            else:
                self.log_test("Porter Registration", False, "Missing token or user in response", response)
        else:
            self.log_test("Porter Registration", False, f"Registration failed (Status: {status_code})", response)
        
        # Test duplicate registration
        success, response, status_code = self.make_request("POST", "/auth/register", customer_data)
        if status_code == 400:
            self.log_test("Duplicate Registration Prevention", True, "Duplicate registration correctly rejected")
        else:
            self.log_test("Duplicate Registration Prevention", False, f"Should reject duplicate (Status: {status_code})", response)
    
    def test_user_login(self):
        """Test login functionality with valid/invalid credentials"""
        print("\n=== Testing User Login ===")
        
        # Test valid customer login
        login_data = {
            "email": "john.doe@example.com",
            "password": "securepass123"
        }
        
        success, response, status_code = self.make_request("POST", "/auth/login", login_data)
        
        if success and status_code == 200:
            if "access_token" in response:
                self.log_test("Customer Login", True, "Customer login successful")
                # Update token if needed
                if not self.customer_token:
                    self.customer_token = response["access_token"]
                    self.customer_user = response["user"]
            else:
                self.log_test("Customer Login", False, "Missing access token in response", response)
        else:
            self.log_test("Customer Login", False, f"Login failed (Status: {status_code})", response)
        
        # Test invalid credentials
        invalid_login = {
            "email": "john.doe@example.com",
            "password": "wrongpassword"
        }
        
        success, response, status_code = self.make_request("POST", "/auth/login", invalid_login)
        if status_code == 401:
            self.log_test("Invalid Credentials Rejection", True, "Invalid credentials correctly rejected")
        else:
            self.log_test("Invalid Credentials Rejection", False, f"Should reject invalid credentials (Status: {status_code})", response)
    
    def test_static_porter_accounts(self):
        """Test static porter account initialization and login"""
        print("\n=== Testing Static Porter Accounts ===")
        
        static_porters = [
            {"email": "porter1@luggixx.com", "name": "Raj Kumar"},
            {"email": "porter2@luggixx.com", "name": "Amit Singh"},
            {"email": "porter3@luggixx.com", "name": "Vikram Yadav"},
            {"email": "porter4@luggixx.com", "name": "Suresh Patel"},
            {"email": "porter5@luggixx.com", "name": "Ramesh Gupta"}
        ]
        
        successful_logins = 0
        
        for porter in static_porters:
            login_data = {
                "email": porter["email"],
                "password": "password123"
            }
            
            success, response, status_code = self.make_request("POST", "/auth/login", login_data)
            
            if success and status_code == 200:
                if "access_token" in response and response["user"]["role"] == "porter":
                    successful_logins += 1
                    # Store first porter token for later tests
                    if not self.porter_token:
                        self.porter_token = response["access_token"]
                        self.porter_user = response["user"]
                    self.log_test(f"Static Porter Login ({porter['name']})", True, f"Login successful for {porter['name']}")
                else:
                    self.log_test(f"Static Porter Login ({porter['name']})", False, "Invalid response format", response)
            else:
                self.log_test(f"Static Porter Login ({porter['name']})", False, f"Login failed (Status: {status_code})", response)
        
        if successful_logins == 5:
            self.log_test("All Static Porter Accounts", True, "All 5 static porter accounts working")
        else:
            self.log_test("All Static Porter Accounts", False, f"Only {successful_logins}/5 porter accounts working")
    
    def test_jwt_token_validation(self):
        """Test JWT token validation for protected endpoints"""
        print("\n=== Testing JWT Token Validation ===")
        
        # Test valid token
        if self.customer_token:
            headers = self.get_auth_headers(self.customer_token)
            success, response, status_code = self.make_request("GET", "/auth/me", headers=headers)
            
            if success and status_code == 200:
                self.log_test("Valid Token Access", True, "Protected endpoint accessible with valid token")
            else:
                self.log_test("Valid Token Access", False, f"Valid token rejected (Status: {status_code})", response)
        
        # Test invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        success, response, status_code = self.make_request("GET", "/auth/me", headers=invalid_headers)
        
        if status_code == 401:
            self.log_test("Invalid Token Rejection", True, "Invalid token correctly rejected")
        else:
            self.log_test("Invalid Token Rejection", False, f"Should reject invalid token (Status: {status_code})", response)
        
        # Test missing token
        success, response, status_code = self.make_request("GET", "/auth/me")
        
        if status_code in [401, 403]:
            self.log_test("Missing Token Rejection", True, "Missing token correctly rejected")
        else:
            self.log_test("Missing Token Rejection", False, f"Should reject missing token (Status: {status_code})", response)
    
    def test_ride_request_creation(self):
        """Test customer can create ride requests successfully"""
        print("\n=== Testing Ride Request Creation ===")
        
        if not self.customer_token:
            self.log_test("Ride Request Creation", False, "No customer token available for testing")
            return
        
        ride_data = {
            "pickup_location": "Mumbai Central Station",
            "destination": "Chhatrapati Shivaji Airport"
        }
        
        headers = self.get_auth_headers(self.customer_token)
        success, response, status_code = self.make_request("POST", "/rides/request", ride_data, headers)
        
        if success and status_code == 200:
            if "id" in response and "porter_id" in response and response["status"] == "assigned":
                self.test_ride_id = response["id"]
                self.assigned_porter_id = response["porter_id"]
                self.log_test("Ride Request Creation", True, "Ride request created and auto-assigned successfully")
                self.log_test("Auto-Assignment", True, f"Ride auto-assigned to porter: {response.get('porter_name', 'Unknown')}")
            else:
                self.log_test("Ride Request Creation", False, "Invalid response format or missing assignment", response)
        else:
            self.log_test("Ride Request Creation", False, f"Ride request failed (Status: {status_code})", response)
    
    def test_role_based_access_control(self):
        """Test role-based access control restrictions"""
        print("\n=== Testing Role-Based Access Control ===")
        
        # Test porter trying to create ride request (should fail)
        if self.porter_token:
            ride_data = {
                "pickup_location": "Test Location",
                "destination": "Test Destination"
            }
            
            headers = self.get_auth_headers(self.porter_token)
            success, response, status_code = self.make_request("POST", "/rides/request", ride_data, headers)
            
            if status_code == 403:
                self.log_test("Porter Ride Request Restriction", True, "Porter correctly prevented from creating ride requests")
            else:
                self.log_test("Porter Ride Request Restriction", False, f"Porter should not be able to create rides (Status: {status_code})", response)
        
        # Test customer trying to update ride status (should work for their own rides)
        if self.customer_token and self.test_ride_id:
            headers = self.get_auth_headers(self.customer_token)
            success, response, status_code = self.make_request("PUT", f"/rides/{self.test_ride_id}/status?status=cancelled", headers=headers)
            
            if success and status_code == 200:
                self.log_test("Customer Ride Status Update", True, "Customer can update their own ride status")
            else:
                self.log_test("Customer Ride Status Update", False, f"Customer should be able to update own rides (Status: {status_code})", response)
    
    def test_ride_status_updates(self):
        """Test ride status updates by porters"""
        print("\n=== Testing Ride Status Updates ===")
        
        if not self.porter_token or not self.test_ride_id:
            self.log_test("Ride Status Updates", False, "No porter token or test ride available")
            return
        
        # Test porter updating ride status to in_progress
        headers = self.get_auth_headers(self.porter_token)
        success, response, status_code = self.make_request("PUT", f"/rides/{self.test_ride_id}/status?status=in_progress", headers=headers)
        
        if success and status_code == 200:
            self.log_test("Porter Status Update (In Progress)", True, "Porter successfully updated ride to in_progress")
        else:
            self.log_test("Porter Status Update (In Progress)", False, f"Porter status update failed (Status: {status_code})", response)
        
        # Test porter updating ride status to completed
        success, response, status_code = self.make_request("PUT", f"/rides/{self.test_ride_id}/status?status=completed", headers=headers)
        
        if success and status_code == 200:
            self.log_test("Porter Status Update (Completed)", True, "Porter successfully updated ride to completed")
        else:
            self.log_test("Porter Status Update (Completed)", False, f"Porter status update failed (Status: {status_code})", response)
    
    def test_ride_retrieval(self):
        """Test ride retrieval for both customers and porters"""
        print("\n=== Testing Ride Retrieval ===")
        
        # Test customer retrieving their rides
        if self.customer_token:
            headers = self.get_auth_headers(self.customer_token)
            success, response, status_code = self.make_request("GET", "/rides/my-rides", headers=headers)
            
            if success and status_code == 200:
                if isinstance(response, list):
                    self.log_test("Customer Ride Retrieval", True, f"Customer retrieved {len(response)} rides")
                else:
                    self.log_test("Customer Ride Retrieval", False, "Response should be a list", response)
            else:
                self.log_test("Customer Ride Retrieval", False, f"Ride retrieval failed (Status: {status_code})", response)
        
        # Test porter retrieving their rides
        if self.porter_token:
            headers = self.get_auth_headers(self.porter_token)
            success, response, status_code = self.make_request("GET", "/rides/my-rides", headers=headers)
            
            if success and status_code == 200:
                if isinstance(response, list):
                    self.log_test("Porter Ride Retrieval", True, f"Porter retrieved {len(response)} rides")
                else:
                    self.log_test("Porter Ride Retrieval", False, "Response should be a list", response)
            else:
                self.log_test("Porter Ride Retrieval", False, f"Ride retrieval failed (Status: {status_code})", response)
    
    def test_available_porters_endpoint(self):
        """Test available porters endpoint"""
        print("\n=== Testing Available Porters Endpoint ===")
        
        success, response, status_code = self.make_request("GET", "/porters/available")
        
        if success and status_code == 200:
            if isinstance(response, list) and len(response) >= 5:
                self.log_test("Available Porters Endpoint", True, f"Retrieved {len(response)} available porters")
            else:
                self.log_test("Available Porters Endpoint", False, f"Expected at least 5 porters, got {len(response) if isinstance(response, list) else 'invalid format'}", response)
        else:
            self.log_test("Available Porters Endpoint", False, f"Endpoint failed (Status: {status_code})", response)
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Luggixx Backend API Tests")
        print(f"🔗 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Run tests in logical order
        self.test_user_registration()
        self.test_user_login()
        self.test_static_porter_accounts()
        self.test_jwt_token_validation()
        self.test_available_porters_endpoint()
        self.test_ride_request_creation()
        self.test_role_based_access_control()
        self.test_ride_status_updates()
        self.test_ride_retrieval()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    tester = LuggixxAPITester()
    tester.run_all_tests()