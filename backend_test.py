#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import time

class SalesBrainAPITester:
    def __init__(self, base_url="https://salesgenius-17.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.user_id = None
        self.customer_id = None
        self.product_id = None
        self.conversation_id = None
        self.order_id = None

    def log_result(self, test_name, success, response_data=None, error=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name} - PASSED")
        else:
            self.failed_tests.append({"test": test_name, "error": error})
            print(f"❌ {test_name} - FAILED: {error}")
        
        if response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text[:500]}

            return success, response_data, response.status_code

        except Exception as e:
            return False, {}, str(e)

    def test_health_check(self):
        """Test API health check"""
        success, data, status = self.make_request('GET', '')
        self.log_result("Health Check", success, data, f"Status: {status}")
        return success

    def test_user_registration(self):
        """Test user registration"""
        test_user = {
            "name": "Test User",
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPass123!",
            "role": "admin"
        }
        
        success, data, status = self.make_request('POST', 'auth/register', test_user, 200)
        
        if success and 'token' in data:
            self.token = data['token']
            self.user_id = data.get('user', {}).get('id')
            
        self.log_result("User Registration", success, data, f"Status: {status}")
        return success

    def test_user_login(self):
        """Test user login with existing credentials"""
        login_data = {
            "email": "admin@salesbrain.com",
            "password": "admin123"
        }
        
        success, data, status = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success and 'token' in data:
            self.token = data['token']
            self.user_id = data.get('user', {}).get('id')
            
        self.log_result("User Login", success, data, f"Status: {status}")
        return success

    def test_get_user_profile(self):
        """Test getting current user profile"""
        success, data, status = self.make_request('GET', 'auth/me', expected_status=200)
        self.log_result("Get User Profile", success, data, f"Status: {status}")
        return success

    def test_seed_data(self):
        """Test seeding sample data"""
        success, data, status = self.make_request('POST', 'seed', expected_status=200)
        self.log_result("Seed Data", success, data, f"Status: {status}")
        return success

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        success, data, status = self.make_request('GET', 'dashboard/stats', expected_status=200)
        self.log_result("Dashboard Stats", success, data, f"Status: {status}")
        return success

    def test_customers_crud(self):
        """Test customer CRUD operations"""
        # Create customer
        customer_data = {
            "name": "Test Customer",
            "email": "testcustomer@example.com",
            "phone": "+91 98765 99999",
            "customer_type": "individual",
            "notes": "Test customer for API testing"
        }
        
        success, data, status = self.make_request('POST', 'customers', customer_data, 200)
        if success and 'id' in data:
            self.customer_id = data['id']
        self.log_result("Create Customer", success, data, f"Status: {status}")
        
        if not success:
            return False

        # Get customers list
        success, data, status = self.make_request('GET', 'customers', expected_status=200)
        self.log_result("Get Customers List", success, data, f"Status: {status}")
        
        # Get specific customer
        if self.customer_id:
            success, data, status = self.make_request('GET', f'customers/{self.customer_id}', expected_status=200)
            self.log_result("Get Specific Customer", success, data, f"Status: {status}")
            
            # Update customer
            update_data = {"notes": "Updated notes for testing"}
            success, data, status = self.make_request('PUT', f'customers/{self.customer_id}', update_data, 200)
            self.log_result("Update Customer", success, data, f"Status: {status}")

        return True

    def test_products_crud(self):
        """Test product CRUD operations"""
        # Create product
        product_data = {
            "name": "Test Product",
            "description": "A test product for API testing",
            "category": "Smartphones",
            "sku": "TEST-PROD-001",
            "base_price": 50000.0,
            "tax_rate": 18.0,
            "stock": 10
        }
        
        success, data, status = self.make_request('POST', 'products', product_data, 200)
        if success and 'id' in data:
            self.product_id = data['id']
        self.log_result("Create Product", success, data, f"Status: {status}")
        
        if not success:
            return False

        # Get products list
        success, data, status = self.make_request('GET', 'products', expected_status=200)
        self.log_result("Get Products List", success, data, f"Status: {status}")
        
        # Get specific product
        if self.product_id:
            success, data, status = self.make_request('GET', f'products/{self.product_id}', expected_status=200)
            self.log_result("Get Specific Product", success, data, f"Status: {status}")

        return True

    def test_conversations_and_messages(self):
        """Test conversations and messaging"""
        if not self.customer_id:
            print("⚠️  Skipping conversation tests - no customer ID available")
            return False

        # Create topic (which creates conversation)
        topic_data = {
            "customer_id": self.customer_id,
            "topic_type": "product_inquiry",
            "title": "Test Product Inquiry"
        }
        
        success, data, status = self.make_request('POST', 'topics', topic_data, 200)
        self.log_result("Create Topic", success, data, f"Status: {status}")
        
        # Get conversations
        success, data, status = self.make_request('GET', 'conversations', expected_status=200)
        if success and data and len(data) > 0:
            self.conversation_id = data[0]['id']
        self.log_result("Get Conversations", success, data, f"Status: {status}")
        
        # Send message if we have conversation
        if self.conversation_id:
            message_data = {
                "conversation_id": self.conversation_id,
                "content": "Hello, I want to inquire about products",
                "sender_type": "customer",
                "message_type": "text"
            }
            
            success, data, status = self.make_request('POST', f'conversations/{self.conversation_id}/messages', message_data, 200)
            self.log_result("Send Message", success, data, f"Status: {status}")
            
            # Get messages
            success, data, status = self.make_request('GET', f'conversations/{self.conversation_id}/messages', expected_status=200)
            self.log_result("Get Messages", success, data, f"Status: {status}")

        return True

    def test_ai_chat(self):
        """Test AI chat functionality"""
        if not self.customer_id or not self.conversation_id:
            print("⚠️  Skipping AI chat test - missing customer or conversation ID")
            return False

        ai_request = {
            "customer_id": self.customer_id,
            "conversation_id": self.conversation_id,
            "message": "I want to buy iPhone 15 Pro Max"
        }
        
        print("🤖 Testing AI chat (this may take a few seconds)...")
        success, data, status = self.make_request('POST', 'ai/chat', ai_request, 200)
        self.log_result("AI Chat", success, data, f"Status: {status}")
        
        if success and 'response' in data:
            print(f"   AI Response: {data['response'][:100]}...")
            
        return success

    def test_orders_crud(self):
        """Test order operations"""
        if not self.customer_id or not self.product_id:
            print("⚠️  Skipping order tests - missing customer or product ID")
            return False

        # Create order
        order_data = {
            "customer_id": self.customer_id,
            "conversation_id": self.conversation_id,
            "items": [
                {
                    "product_id": self.product_id,
                    "quantity": 1,
                    "price": 50000.0
                }
            ],
            "shipping_address": {
                "type": "home",
                "address": "123 Test Street, Test City 560001"
            },
            "notes": "Test order"
        }
        
        success, data, status = self.make_request('POST', 'orders', order_data, 200)
        if success and 'id' in data:
            self.order_id = data['id']
        self.log_result("Create Order", success, data, f"Status: {status}")
        
        # Get orders
        success, data, status = self.make_request('GET', 'orders', expected_status=200)
        self.log_result("Get Orders", success, data, f"Status: {status}")
        
        # Update order status
        if self.order_id:
            success, data, status = self.make_request('PUT', f'orders/{self.order_id}/status?status=confirmed', expected_status=200)
            self.log_result("Update Order Status", success, data, f"Status: {status}")

        return True

    def test_tickets(self):
        """Test ticket operations (osTicket mock)"""
        # Get tickets
        success, data, status = self.make_request('GET', 'tickets', expected_status=200)
        self.log_result("Get Tickets", success, data, f"Status: {status}")
        return success

    def test_whatsapp_integration(self):
        """Test WhatsApp integration (mocked)"""
        # Get WhatsApp status
        success, data, status = self.make_request('GET', 'whatsapp/status', expected_status=200)
        self.log_result("WhatsApp Status", success, data, f"Status: {status}")
        
        # Connect WhatsApp
        success, data, status = self.make_request('POST', 'whatsapp/connect', expected_status=200)
        self.log_result("WhatsApp Connect", success, data, f"Status: {status}")
        
        # Simulate message
        success, data, status = self.make_request('POST', 'whatsapp/simulate-message?phone=%2B91%2098765%2000001&message=Hello%20from%20test', expected_status=200)
        self.log_result("WhatsApp Simulate Message", success, data, f"Status: {status}")
        
        return True

    def test_settings(self):
        """Test settings operations"""
        # Get settings
        success, data, status = self.make_request('GET', 'settings', expected_status=200)
        self.log_result("Get Settings", success, data, f"Status: {status}")
        
        # Update settings
        settings_data = {
            "business_name": "Test Sales Brain",
            "ai_enabled": True,
            "auto_reply": True
        }
        success, data, status = self.make_request('PUT', 'settings', settings_data, 200)
        self.log_result("Update Settings", success, data, f"Status: {status}")
        
        return True

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Sales Brain API Tests")
        print("=" * 50)
        
        # Test sequence
        tests = [
            ("Health Check", self.test_health_check),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Get User Profile", self.test_get_user_profile),
            ("Seed Data", self.test_seed_data),
            ("Dashboard Stats", self.test_dashboard_stats),
            ("Customer CRUD", self.test_customers_crud),
            ("Product CRUD", self.test_products_crud),
            ("Conversations & Messages", self.test_conversations_and_messages),
            ("AI Chat", self.test_ai_chat),
            ("Orders CRUD", self.test_orders_crud),
            ("Tickets", self.test_tickets),
            ("WhatsApp Integration", self.test_whatsapp_integration),
            ("Settings", self.test_settings),
        ]
        
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                test_func()
            except Exception as e:
                self.log_result(test_name, False, error=str(e))
            
            time.sleep(0.5)  # Small delay between tests
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for failed in self.failed_tests:
                print(f"  - {failed['test']}: {failed['error']}")
        
        return len(self.failed_tests) == 0

def main():
    tester = SalesBrainAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())