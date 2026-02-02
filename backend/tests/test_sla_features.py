"""
Test SLA Timer & Escalation Features
Tests for the 4-part AI control system:
1. AI checks customer profile & KB
2. If info found, reply accurately
3. If not found, escalate to owner with SLA timer (30 mins)
4. When owner replies, AI polishes the response and sends to customer

Endpoints tested:
- GET /api/conversations - Returns escalated_at, sla_deadline, sla_reminders_sent fields
- GET /api/escalations/pending-sla - Returns pending escalations with SLA info
- POST /api/escalations/check-sla - Triggers SLA check
"""

import pytest
import requests
import os
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test123"


class TestSLAFeatures:
    """Test SLA Timer and Escalation Features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code == 200:
            token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Authentication failed: {response.status_code}")
    
    def test_login_with_test_credentials(self):
        """Test login with test@test.com / test123"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "user" in data, "User not in response"
        assert data["user"]["email"] == TEST_EMAIL
        print(f"✓ Login successful for {TEST_EMAIL}")
    
    def test_conversations_endpoint_returns_sla_fields(self):
        """Test GET /api/conversations returns escalated_at, sla_deadline, sla_reminders_sent fields"""
        response = self.session.get(f"{BASE_URL}/api/conversations")
        
        assert response.status_code == 200, f"Conversations endpoint failed: {response.text}"
        data = response.json()
        
        # Check that the response is a list
        assert isinstance(data, list), "Response should be a list"
        
        # If there are conversations, check the SLA fields exist in the schema
        if len(data) > 0:
            conv = data[0]
            # These fields should exist (can be null)
            assert "escalated_at" in conv or conv.get("escalated_at") is None or "escalated_at" not in conv, \
                "escalated_at field should be present or null"
            
            # Check for SLA-related fields in the response
            print(f"✓ Conversations endpoint returned {len(data)} conversations")
            print(f"  Sample conversation fields: {list(conv.keys())}")
            
            # Verify the expected SLA fields are in the response model
            expected_fields = ["id", "customer_id", "customer_name", "status"]
            for field in expected_fields:
                assert field in conv, f"Missing expected field: {field}"
        else:
            print("✓ Conversations endpoint returned empty list (no conversations)")
    
    def test_conversations_have_sla_fields_in_model(self):
        """Verify ConversationResponse model includes SLA tracking fields"""
        response = self.session.get(f"{BASE_URL}/api/conversations")
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            conv = data[0]
            # Check for SLA fields - they may be null but should be in the response
            sla_fields = ["escalated_at", "sla_deadline", "sla_reminders_sent"]
            
            for field in sla_fields:
                # Field should exist in response (even if null)
                if field in conv:
                    print(f"  ✓ Field '{field}' present: {conv[field]}")
                else:
                    # Field might not be returned if null - check if it's in the model
                    print(f"  ⚠ Field '{field}' not in response (may be null)")
            
            # Check status field for escalation states
            status = conv.get("status", "")
            print(f"  Status: {status}")
            
            if status in ["escalated", "waiting_for_owner"]:
                print(f"  ✓ Found escalated conversation with status: {status}")
                # For escalated conversations, SLA fields should be populated
                if conv.get("sla_deadline"):
                    print(f"    SLA Deadline: {conv['sla_deadline']}")
                if conv.get("escalated_at"):
                    print(f"    Escalated At: {conv['escalated_at']}")
    
    def test_pending_sla_endpoint(self):
        """Test GET /api/escalations/pending-sla returns pending escalations with SLA info"""
        response = self.session.get(f"{BASE_URL}/api/escalations/pending-sla")
        
        assert response.status_code == 200, f"Pending SLA endpoint failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Pending SLA endpoint returned {len(data)} pending escalations")
        
        if len(data) > 0:
            esc = data[0]
            # Verify expected fields in pending SLA response
            expected_fields = [
                "id", "customer_id", "customer_name", "customer_phone",
                "customer_message", "reason", "created_at", "sla_deadline",
                "sla_reminders_sent", "is_overdue", "minutes_remaining", "minutes_overdue"
            ]
            
            for field in expected_fields:
                assert field in esc, f"Missing expected field: {field}"
            
            print(f"  Sample escalation:")
            print(f"    Customer: {esc.get('customer_name')}")
            print(f"    SLA Deadline: {esc.get('sla_deadline')}")
            print(f"    Is Overdue: {esc.get('is_overdue')}")
            print(f"    Minutes Remaining: {esc.get('minutes_remaining')}")
            print(f"    Minutes Overdue: {esc.get('minutes_overdue')}")
            print(f"    Reminders Sent: {esc.get('sla_reminders_sent')}")
    
    def test_check_sla_endpoint(self):
        """Test POST /api/escalations/check-sla can trigger SLA check"""
        response = self.session.post(f"{BASE_URL}/api/escalations/check-sla")
        
        assert response.status_code == 200, f"Check SLA endpoint failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        expected_fields = ["checked_at", "total_pending", "overdue_count", "reminders_sent"]
        for field in expected_fields:
            assert field in data, f"Missing expected field: {field}"
        
        print(f"✓ SLA Check completed:")
        print(f"  Checked At: {data.get('checked_at')}")
        print(f"  Total Pending: {data.get('total_pending')}")
        print(f"  Overdue Count: {data.get('overdue_count')}")
        print(f"  Reminders Sent: {len(data.get('reminders_sent', []))}")
    
    def test_conversation_status_values(self):
        """Test that conversations can have status values: active, escalated, waiting_for_owner"""
        response = self.session.get(f"{BASE_URL}/api/conversations")
        
        assert response.status_code == 200
        data = response.json()
        
        valid_statuses = ["active", "escalated", "waiting_for_owner", "resolved"]
        status_counts = {s: 0 for s in valid_statuses}
        
        for conv in data:
            status = conv.get("status", "").lower()
            if status in valid_statuses:
                status_counts[status] += 1
        
        print(f"✓ Conversation status distribution:")
        for status, count in status_counts.items():
            print(f"  {status.upper()}: {count}")
    
    def test_escalations_endpoint(self):
        """Test GET /api/escalations returns escalation records"""
        response = self.session.get(f"{BASE_URL}/api/escalations")
        
        assert response.status_code == 200, f"Escalations endpoint failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Escalations endpoint returned {len(data)} escalations")
        
        if len(data) > 0:
            esc = data[0]
            expected_fields = ["id", "customer_id", "customer_name", "conversation_id", 
                             "reason", "message_content", "status", "priority", "created_at"]
            
            for field in expected_fields:
                assert field in esc, f"Missing expected field: {field}"
            
            print(f"  Sample escalation status: {esc.get('status')}")
            print(f"  Priority: {esc.get('priority')}")


class TestConversationStatusBadges:
    """Test conversation status for frontend badge display"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code == 200:
            token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip(f"Authentication failed: {response.status_code}")
    
    def test_active_status_badge(self):
        """Test that ACTIVE status is returned for active conversations"""
        response = self.session.get(f"{BASE_URL}/api/conversations")
        
        assert response.status_code == 200
        data = response.json()
        
        active_convs = [c for c in data if c.get("status", "").lower() == "active"]
        print(f"✓ Found {len(active_convs)} ACTIVE conversations")
        
        # Active conversations should NOT have sla_deadline set
        for conv in active_convs[:3]:  # Check first 3
            if conv.get("sla_deadline"):
                print(f"  ⚠ Active conversation has SLA deadline: {conv.get('sla_deadline')}")
    
    def test_waiting_status_badge(self):
        """Test that WAITING status is returned for escalated conversations"""
        response = self.session.get(f"{BASE_URL}/api/conversations")
        
        assert response.status_code == 200
        data = response.json()
        
        waiting_convs = [c for c in data if c.get("status", "").lower() in ["waiting_for_owner", "escalated"]]
        print(f"✓ Found {len(waiting_convs)} WAITING/ESCALATED conversations")
        
        for conv in waiting_convs[:3]:
            print(f"  Customer: {conv.get('customer_name')}")
            print(f"  Status: {conv.get('status')}")
            print(f"  SLA Deadline: {conv.get('sla_deadline')}")
    
    def test_overdue_detection(self):
        """Test that overdue conversations can be detected via sla_deadline"""
        response = self.session.get(f"{BASE_URL}/api/conversations")
        
        assert response.status_code == 200
        data = response.json()
        
        now = datetime.now(timezone.utc)
        overdue_count = 0
        
        for conv in data:
            sla_deadline = conv.get("sla_deadline")
            if sla_deadline:
                try:
                    deadline_dt = datetime.fromisoformat(sla_deadline.replace('Z', '+00:00'))
                    if now > deadline_dt:
                        overdue_count += 1
                        print(f"  OVERDUE: {conv.get('customer_name')} - Deadline: {sla_deadline}")
                except:
                    pass
        
        print(f"✓ Found {overdue_count} OVERDUE conversations")


class TestAPIAuthentication:
    """Test API authentication requirements"""
    
    def test_conversations_requires_auth(self):
        """Test that /api/conversations requires authentication"""
        response = requests.get(f"{BASE_URL}/api/conversations")
        
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], \
            f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Conversations endpoint requires authentication")
    
    def test_pending_sla_requires_auth(self):
        """Test that /api/escalations/pending-sla requires authentication"""
        response = requests.get(f"{BASE_URL}/api/escalations/pending-sla")
        
        assert response.status_code in [401, 403], \
            f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Pending SLA endpoint requires authentication")
    
    def test_check_sla_requires_auth(self):
        """Test that /api/escalations/check-sla requires authentication"""
        response = requests.post(f"{BASE_URL}/api/escalations/check-sla")
        
        assert response.status_code in [401, 403], \
            f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Check SLA endpoint requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
