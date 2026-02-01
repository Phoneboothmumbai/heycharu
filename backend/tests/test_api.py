"""
Backend API Tests for Sales Brain Platform
Tests: Auth, Customers, Products, Orders, Conversations, WhatsApp, Dashboard, Settings
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = f"test_{uuid.uuid4().hex[:8]}@test.com"
TEST_PASSWORD = "testpass123"
TEST_NAME = "Test User"

# Global token storage
auth_token = None
test_customer_id = None
test_product_id = None
test_conversation_id = None


class TestHealthCheck:
    """Health check tests - run first"""
    
    def test_api_health(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"SUCCESS: API health check passed - {data}")


class TestAuthentication:
    """Authentication flow tests"""
    
    def test_register_new_user(self):
        """Test user registration"""
        global auth_token
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": TEST_NAME,
            "role": "admin"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        auth_token = data["token"]
        print(f"SUCCESS: User registered - {data['user']['email']}")
    
    def test_login_existing_user(self):
        """Test login with registered user"""
        global auth_token
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        auth_token = data["token"]
        print(f"SUCCESS: User logged in - {data['user']['email']}")
    
    def test_login_invalid_credentials(self):
        """Test login with wrong credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@test.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        print("SUCCESS: Invalid credentials rejected correctly")
    
    def test_get_current_user(self):
        """Test getting current user info"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL
        print(f"SUCCESS: Current user retrieved - {data['email']}")


class TestCustomers:
    """Customer CRUD tests"""
    
    def test_create_customer(self):
        """Test creating a new customer"""
        global test_customer_id
        headers = {"Authorization": f"Bearer {auth_token}"}
        customer_data = {
            "name": f"TEST_Customer_{uuid.uuid4().hex[:6]}",
            "phone": f"+91 98765 {uuid.uuid4().hex[:5]}",
            "email": f"test_customer_{uuid.uuid4().hex[:6]}@test.com",
            "customer_type": "individual",
            "notes": "Test customer for API testing"
        }
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == customer_data["name"]
        assert "id" in data
        test_customer_id = data["id"]
        print(f"SUCCESS: Customer created - {data['name']}")
    
    def test_get_customers_list(self):
        """Test getting customers list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/customers", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Retrieved {len(data)} customers")
    
    def test_get_customer_by_id(self):
        """Test getting customer by ID"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/customers/{test_customer_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_customer_id
        print(f"SUCCESS: Customer retrieved by ID - {data['name']}")
    
    def test_update_customer(self):
        """Test updating customer"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        update_data = {"notes": "Updated notes for testing"}
        response = requests.put(f"{BASE_URL}/api/customers/{test_customer_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == update_data["notes"]
        print(f"SUCCESS: Customer updated - {data['name']}")
    
    def test_search_customers(self):
        """Test customer search"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/customers?search=TEST", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Customer search returned {len(data)} results")


class TestProducts:
    """Product CRUD tests"""
    
    def test_create_product(self):
        """Test creating a new product"""
        global test_product_id
        headers = {"Authorization": f"Bearer {auth_token}"}
        product_data = {
            "name": f"TEST_Product_{uuid.uuid4().hex[:6]}",
            "description": "Test product for API testing",
            "category": "Smartphones",
            "sku": f"TEST-SKU-{uuid.uuid4().hex[:6]}",
            "base_price": 99999.0,
            "tax_rate": 18.0,
            "stock": 10
        }
        response = requests.post(f"{BASE_URL}/api/products", json=product_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == product_data["name"]
        assert "id" in data
        assert "final_price" in data
        test_product_id = data["id"]
        print(f"SUCCESS: Product created - {data['name']} (Final price: {data['final_price']})")
    
    def test_get_products_list(self):
        """Test getting products list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Retrieved {len(data)} products")
    
    def test_get_product_by_id(self):
        """Test getting product by ID"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/products/{test_product_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_product_id
        print(f"SUCCESS: Product retrieved by ID - {data['name']}")
    
    def test_update_product(self):
        """Test updating product"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        update_data = {
            "name": f"TEST_Updated_Product_{uuid.uuid4().hex[:6]}",
            "description": "Updated description",
            "category": "Smartphones",
            "sku": f"TEST-SKU-{uuid.uuid4().hex[:6]}",
            "base_price": 89999.0,
            "tax_rate": 18.0,
            "stock": 15
        }
        response = requests.put(f"{BASE_URL}/api/products/{test_product_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["base_price"] == update_data["base_price"]
        print(f"SUCCESS: Product updated - {data['name']}")


class TestConversations:
    """Conversation and messaging tests"""
    
    def test_get_conversations(self):
        """Test getting conversations list"""
        global test_conversation_id
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/conversations", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            test_conversation_id = data[0]["id"]
        print(f"SUCCESS: Retrieved {len(data)} conversations")
    
    def test_get_conversation_messages(self):
        """Test getting messages for a conversation"""
        if not test_conversation_id:
            pytest.skip("No conversation available")
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/conversations/{test_conversation_id}/messages", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Retrieved {len(data)} messages")


class TestOrders:
    """Order management tests"""
    
    def test_get_orders(self):
        """Test getting orders list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/orders", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Retrieved {len(data)} orders")
    
    def test_get_tickets(self):
        """Test getting tickets list (osTicket MOCKED)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/tickets", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Retrieved {len(data)} tickets (MOCKED)")


class TestWhatsApp:
    """WhatsApp integration tests (Preview Mode)"""
    
    def test_whatsapp_status(self):
        """Test WhatsApp status endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/whatsapp/status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "connected" in data or "status" in data
        print(f"SUCCESS: WhatsApp status - {data.get('status', 'unknown')}, previewMode: {data.get('previewMode', False)}")
    
    def test_simulate_whatsapp_message(self):
        """Test WhatsApp message simulation"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        test_phone = f"+91 98765 {uuid.uuid4().hex[:5]}"
        test_message = "Hi, I need help with my order"
        response = requests.post(
            f"{BASE_URL}/api/whatsapp/simulate-message?phone={test_phone}&message={test_message}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "customer_id" in data
        assert "conversation_id" in data
        print(f"SUCCESS: WhatsApp message simulated - customer_id: {data['customer_id'][:8]}...")


class TestDashboard:
    """Dashboard stats tests"""
    
    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_customers" in data
        assert "active_conversations" in data
        assert "open_topics" in data
        assert "pending_orders" in data
        assert "total_revenue" in data
        print(f"SUCCESS: Dashboard stats - Customers: {data['total_customers']}, Conversations: {data['active_conversations']}, Revenue: {data['total_revenue']}")


class TestSettings:
    """Settings management tests"""
    
    def test_get_settings(self):
        """Test getting settings"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/settings", headers=headers)
        # Settings endpoint may return 200 or create default settings
        assert response.status_code in [200, 201]
        data = response.json()
        assert "business_name" in data or "type" in data
        print(f"SUCCESS: Settings retrieved - {data.get('business_name', 'Sales Brain')}")
    
    def test_update_settings(self):
        """Test updating settings"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        settings_data = {
            "business_name": "Test Sales Brain",
            "ai_enabled": True,
            "auto_reply": True
        }
        response = requests.put(f"{BASE_URL}/api/settings", json=settings_data, headers=headers)
        assert response.status_code == 200
        print("SUCCESS: Settings updated")


class TestKnowledgeBase:
    """Knowledge Base tests"""
    
    def test_get_kb_articles(self):
        """Test getting KB articles"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/kb", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Retrieved {len(data)} KB articles")


class TestEscalations:
    """Escalation management tests"""
    
    def test_get_escalations(self):
        """Test getting escalations"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/escalations", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Retrieved {len(data)} escalations")


class TestCleanup:
    """Cleanup test data"""
    
    def test_delete_test_product(self):
        """Delete test product"""
        if not test_product_id:
            pytest.skip("No test product to delete")
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.delete(f"{BASE_URL}/api/products/{test_product_id}", headers=headers)
        assert response.status_code == 200
        print(f"SUCCESS: Test product deleted")
    
    def test_delete_test_customer(self):
        """Delete test customer"""
        if not test_customer_id:
            pytest.skip("No test customer to delete")
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.delete(f"{BASE_URL}/api/customers/{test_customer_id}", headers=headers)
        assert response.status_code == 200
        print(f"SUCCESS: Test customer deleted")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
