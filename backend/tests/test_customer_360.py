"""
Customer 360° View API Tests
Tests for the comprehensive customer dashboard feature
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCustomer360:
    """Customer 360° View endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo@test.com",
            "password": "demo123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Get a customer ID for testing
        customers_response = self.session.get(f"{BASE_URL}/api/customers")
        assert customers_response.status_code == 200
        customers = customers_response.json()
        assert len(customers) > 0, "No customers found for testing"
        self.customer_id = customers[0]["id"]
        self.customer_name = customers[0]["name"]
    
    def test_get_customer_360_success(self):
        """Test GET /api/customers/{id}/360 returns comprehensive data"""
        response = self.session.get(f"{BASE_URL}/api/customers/{self.customer_id}/360")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify customer data
        assert "customer" in data
        assert data["customer"]["id"] == self.customer_id
        assert data["customer"]["name"] == self.customer_name
        
        # Verify statistics
        assert "statistics" in data
        stats = data["statistics"]
        assert "total_orders" in stats
        assert "total_spent" in stats
        assert "pending_orders" in stats
        assert "completed_orders" in stats
        assert "active_topics" in stats
        assert "resolved_topics" in stats
        assert "total_conversations" in stats
        assert "open_tickets" in stats
        assert "escalations" in stats
        
        # Verify topics arrays
        assert "active_topics" in data
        assert "resolved_topics" in data
        assert isinstance(data["active_topics"], list)
        assert isinstance(data["resolved_topics"], list)
        
        # Verify orders, tickets, escalations
        assert "orders" in data
        assert "tickets" in data
        assert "escalations" in data
        
        # Verify messages and conversations
        assert "recent_messages" in data
        assert "conversations" in data
        
        # Verify exclusion and lead info
        assert "is_excluded" in data
        assert "exclusion_info" in data
        assert "lead_info" in data
        
        print(f"✓ Customer 360° data retrieved for {self.customer_name}")
    
    def test_get_customer_360_not_found(self):
        """Test GET /api/customers/{id}/360 returns 404 for non-existent customer"""
        response = self.session.get(f"{BASE_URL}/api/customers/non-existent-id/360")
        assert response.status_code == 404
        print("✓ 404 returned for non-existent customer")
    
    def test_update_customer_notes(self):
        """Test PUT /api/customers/{id}/notes updates notes"""
        test_note = "Test note from pytest"
        response = self.session.put(
            f"{BASE_URL}/api/customers/{self.customer_id}/notes?notes={test_note}"
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Notes updated"
        
        # Verify via 360 endpoint
        verify_response = self.session.get(f"{BASE_URL}/api/customers/{self.customer_id}/360")
        assert verify_response.status_code == 200
        assert verify_response.json()["customer"]["notes"] == test_note
        
        print("✓ Customer notes updated and verified")
    
    def test_update_customer_tags(self):
        """Test PUT /api/customers/{id}/tags updates tags"""
        test_tags = ["test-tag-1", "test-tag-2"]
        response = self.session.put(
            f"{BASE_URL}/api/customers/{self.customer_id}/tags",
            json=test_tags
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Tags updated"
        
        # Verify via 360 endpoint
        verify_response = self.session.get(f"{BASE_URL}/api/customers/{self.customer_id}/360")
        assert verify_response.status_code == 200
        assert verify_response.json()["customer"]["tags"] == test_tags
        
        print("✓ Customer tags updated and verified")
    
    def test_add_customer_device(self):
        """Test POST /api/customers/{id}/devices adds a device"""
        test_device = {
            "name": "Test iPhone 16",
            "model": "256GB Blue",
            "serial": "TEST-SERIAL-123"
        }
        response = self.session.post(
            f"{BASE_URL}/api/customers/{self.customer_id}/devices",
            json=test_device
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Device added"
        
        # Verify via 360 endpoint
        verify_response = self.session.get(f"{BASE_URL}/api/customers/{self.customer_id}/360")
        assert verify_response.status_code == 200
        devices = verify_response.json()["customer"]["devices"]
        
        # Find the added device
        added_device = None
        for d in devices:
            if d.get("name") == test_device["name"]:
                added_device = d
                break
        
        assert added_device is not None, "Added device not found"
        assert added_device["model"] == test_device["model"]
        assert added_device["serial"] == test_device["serial"]
        assert "added_at" in added_device
        
        print("✓ Customer device added and verified")
    
    def test_remove_customer_device(self):
        """Test DELETE /api/customers/{id}/devices/{index} removes a device"""
        # First add a device to remove
        test_device = {"name": "Device To Remove", "model": "Test"}
        self.session.post(
            f"{BASE_URL}/api/customers/{self.customer_id}/devices",
            json=test_device
        )
        
        # Get current devices to find the index
        verify_response = self.session.get(f"{BASE_URL}/api/customers/{self.customer_id}/360")
        devices = verify_response.json()["customer"]["devices"]
        device_index = len(devices) - 1  # Last device
        
        # Remove the device
        response = self.session.delete(
            f"{BASE_URL}/api/customers/{self.customer_id}/devices/{device_index}"
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Device removed"
        
        # Verify removal
        verify_response = self.session.get(f"{BASE_URL}/api/customers/{self.customer_id}/360")
        new_devices = verify_response.json()["customer"]["devices"]
        assert len(new_devices) == len(devices) - 1
        
        print("✓ Customer device removed and verified")
    
    def test_remove_device_invalid_index(self):
        """Test DELETE /api/customers/{id}/devices/{index} with invalid index"""
        response = self.session.delete(
            f"{BASE_URL}/api/customers/{self.customer_id}/devices/999"
        )
        assert response.status_code == 400
        print("✓ Invalid device index returns 400")
    
    def test_customer_360_statistics_accuracy(self):
        """Test that statistics in 360 view are accurate"""
        response = self.session.get(f"{BASE_URL}/api/customers/{self.customer_id}/360")
        assert response.status_code == 200
        data = response.json()
        
        stats = data["statistics"]
        
        # Verify active_topics count matches array length
        assert stats["active_topics"] >= len(data["active_topics"])
        
        # Verify resolved_topics count matches array length
        assert stats["resolved_topics"] >= len(data["resolved_topics"])
        
        # Verify total_conversations count
        assert stats["total_conversations"] >= len(data["conversations"])
        
        print("✓ Statistics are consistent with data arrays")
    
    def test_customer_360_unauthorized(self):
        """Test GET /api/customers/{id}/360 without auth returns 401/403"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/customers/{self.customer_id}/360")
        assert response.status_code in [401, 403]
        print("✓ Unauthorized access blocked")
    
    @pytest.fixture(autouse=True, scope="function")
    def cleanup(self):
        """Cleanup test data after each test"""
        yield
        # Restore original data if needed
        if hasattr(self, 'session') and hasattr(self, 'customer_id'):
            # Restore notes
            self.session.put(
                f"{BASE_URL}/api/customers/{self.customer_id}/notes?notes=Prefers%20evening%20calls"
            )
            # Restore tags
            self.session.put(
                f"{BASE_URL}/api/customers/{self.customer_id}/tags",
                json=["premium", "apple-user"]
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
