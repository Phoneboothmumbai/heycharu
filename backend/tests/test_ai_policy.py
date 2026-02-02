"""
AI Behavior Policy API Tests
Tests for GET, PUT, and POST /api/ai-policy endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001').rstrip('/')

# Test credentials
TEST_EMAIL = "fresh@test.com"
TEST_PASSWORD = "test123"


class TestAIPolicyAPI:
    """AI Behavior Policy endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code != 200:
            # Try registering the user first
            reg_response = self.session.post(f"{BASE_URL}/api/auth/register", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": "Fresh Test User"
            })
            if reg_response.status_code in [200, 201]:
                self.token = reg_response.json().get("token")
            else:
                # Try with alternate credentials
                response = self.session.post(f"{BASE_URL}/api/auth/login", json={
                    "email": "test@test.com",
                    "password": "test123"
                })
                if response.status_code == 200:
                    self.token = response.json().get("token")
                else:
                    pytest.skip("Authentication failed - skipping tests")
        else:
            self.token = response.json().get("token")
        
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    # ============== GET /api/ai-policy Tests ==============
    
    def test_get_ai_policy_returns_200(self):
        """GET /api/ai-policy should return 200 with policy object"""
        response = self.session.get(f"{BASE_URL}/api/ai-policy")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, dict), "Response should be a dictionary"
    
    def test_get_ai_policy_has_required_fields(self):
        """GET /api/ai-policy should return policy with all required fields"""
        response = self.session.get(f"{BASE_URL}/api/ai-policy")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check top-level fields
        assert "enabled" in data, "Policy should have 'enabled' field"
        assert "global_rules" in data, "Policy should have 'global_rules' field"
        assert "states" in data, "Policy should have 'states' field"
        assert "response_rules" in data, "Policy should have 'response_rules' field"
        assert "fallback" in data, "Policy should have 'fallback' field"
        assert "system_triggers" in data, "Policy should have 'system_triggers' field"
    
    def test_get_ai_policy_global_rules_structure(self):
        """GET /api/ai-policy global_rules should have correct structure"""
        response = self.session.get(f"{BASE_URL}/api/ai-policy")
        assert response.status_code == 200
        
        data = response.json()
        global_rules = data.get("global_rules", {})
        
        assert "allowed_topics" in global_rules, "global_rules should have 'allowed_topics'"
        assert "disallowed_behavior" in global_rules, "global_rules should have 'disallowed_behavior'"
        assert isinstance(global_rules["allowed_topics"], list), "allowed_topics should be a list"
        assert isinstance(global_rules["disallowed_behavior"], list), "disallowed_behavior should be a list"
    
    def test_get_ai_policy_states_has_all_five_states(self):
        """GET /api/ai-policy states should have all 5 conversation states"""
        response = self.session.get(f"{BASE_URL}/api/ai-policy")
        assert response.status_code == 200
        
        data = response.json()
        states = data.get("states", {})
        
        required_states = ["GREETING", "INTENT_COLLECTION", "ACTION", "CLOSURE", "ESCALATION"]
        for state in required_states:
            assert state in states, f"States should include '{state}'"
            assert "enabled" in states[state], f"State '{state}' should have 'enabled' field"
    
    def test_get_ai_policy_response_rules_structure(self):
        """GET /api/ai-policy response_rules should have correct structure"""
        response = self.session.get(f"{BASE_URL}/api/ai-policy")
        assert response.status_code == 200
        
        data = response.json()
        response_rules = data.get("response_rules", {})
        
        expected_fields = ["greeting_limit", "question_limit", "max_response_length", "tone", "language", "emoji_usage"]
        for field in expected_fields:
            assert field in response_rules, f"response_rules should have '{field}'"
    
    def test_get_ai_policy_fallback_structure(self):
        """GET /api/ai-policy fallback should have correct structure"""
        response = self.session.get(f"{BASE_URL}/api/ai-policy")
        assert response.status_code == 200
        
        data = response.json()
        fallback = data.get("fallback", {})
        
        expected_types = ["unclear_data", "out_of_scope", "system_error"]
        for fb_type in expected_types:
            assert fb_type in fallback, f"fallback should have '{fb_type}'"
            assert "action" in fallback[fb_type], f"fallback.{fb_type} should have 'action'"
            assert "template" in fallback[fb_type], f"fallback.{fb_type} should have 'template'"
    
    def test_get_ai_policy_system_triggers_structure(self):
        """GET /api/ai-policy system_triggers should have correct structure"""
        response = self.session.get(f"{BASE_URL}/api/ai-policy")
        assert response.status_code == 200
        
        data = response.json()
        triggers = data.get("system_triggers", {})
        
        assert "lead_inject" in triggers, "system_triggers should have 'lead_inject'"
        assert "enabled" in triggers["lead_inject"], "lead_inject should have 'enabled'"
        assert "keywords" in triggers["lead_inject"], "lead_inject should have 'keywords'"
    
    def test_get_ai_policy_requires_auth(self):
        """GET /api/ai-policy should require authentication"""
        # Create new session without auth
        no_auth_session = requests.Session()
        response = no_auth_session.get(f"{BASE_URL}/api/ai-policy")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
    
    # ============== PUT /api/ai-policy Tests ==============
    
    def test_put_ai_policy_saves_changes(self):
        """PUT /api/ai-policy should save policy changes"""
        # First get current policy
        get_response = self.session.get(f"{BASE_URL}/api/ai-policy")
        assert get_response.status_code == 200
        policy = get_response.json()
        
        # Modify a field
        original_enabled = policy.get("enabled", True)
        policy["enabled"] = not original_enabled
        
        # Save changes
        put_response = self.session.put(f"{BASE_URL}/api/ai-policy", json=policy)
        assert put_response.status_code == 200, f"Expected 200, got {put_response.status_code}: {put_response.text}"
        
        # Verify change was saved
        verify_response = self.session.get(f"{BASE_URL}/api/ai-policy")
        assert verify_response.status_code == 200
        updated_policy = verify_response.json()
        assert updated_policy["enabled"] == (not original_enabled), "Policy change was not persisted"
        
        # Restore original value
        policy["enabled"] = original_enabled
        self.session.put(f"{BASE_URL}/api/ai-policy", json=policy)
    
    def test_put_ai_policy_updates_last_updated(self):
        """PUT /api/ai-policy should update last_updated timestamp"""
        # Get current policy
        get_response = self.session.get(f"{BASE_URL}/api/ai-policy")
        policy = get_response.json()
        
        # Save without changes
        put_response = self.session.put(f"{BASE_URL}/api/ai-policy", json=policy)
        assert put_response.status_code == 200
        
        # Verify last_updated was set
        verify_response = self.session.get(f"{BASE_URL}/api/ai-policy")
        updated_policy = verify_response.json()
        assert "last_updated" in updated_policy, "last_updated should be set after PUT"
        assert updated_policy["last_updated"] is not None, "last_updated should not be None"
    
    def test_put_ai_policy_updates_global_rules(self):
        """PUT /api/ai-policy should update global_rules correctly"""
        # Get current policy
        get_response = self.session.get(f"{BASE_URL}/api/ai-policy")
        policy = get_response.json()
        
        # Add a new allowed topic
        original_topics = policy["global_rules"]["allowed_topics"].copy()
        policy["global_rules"]["allowed_topics"].append("test_topic")
        
        # Save changes
        put_response = self.session.put(f"{BASE_URL}/api/ai-policy", json=policy)
        assert put_response.status_code == 200
        
        # Verify change
        verify_response = self.session.get(f"{BASE_URL}/api/ai-policy")
        updated_policy = verify_response.json()
        assert "test_topic" in updated_policy["global_rules"]["allowed_topics"], "New topic should be saved"
        
        # Restore original
        policy["global_rules"]["allowed_topics"] = original_topics
        self.session.put(f"{BASE_URL}/api/ai-policy", json=policy)
    
    def test_put_ai_policy_updates_state_config(self):
        """PUT /api/ai-policy should update state configuration"""
        # Get current policy
        get_response = self.session.get(f"{BASE_URL}/api/ai-policy")
        policy = get_response.json()
        
        # Modify GREETING state
        original_template = policy["states"]["GREETING"].get("response_template", "")
        policy["states"]["GREETING"]["response_template"] = "Test greeting template"
        
        # Save changes
        put_response = self.session.put(f"{BASE_URL}/api/ai-policy", json=policy)
        assert put_response.status_code == 200
        
        # Verify change
        verify_response = self.session.get(f"{BASE_URL}/api/ai-policy")
        updated_policy = verify_response.json()
        assert updated_policy["states"]["GREETING"]["response_template"] == "Test greeting template"
        
        # Restore original
        policy["states"]["GREETING"]["response_template"] = original_template
        self.session.put(f"{BASE_URL}/api/ai-policy", json=policy)
    
    # ============== POST /api/ai-policy/reset Tests ==============
    
    def test_reset_ai_policy_returns_200(self):
        """POST /api/ai-policy/reset should return 200"""
        response = self.session.post(f"{BASE_URL}/api/ai-policy/reset")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_reset_ai_policy_restores_defaults(self):
        """POST /api/ai-policy/reset should restore default values"""
        # First modify the policy
        get_response = self.session.get(f"{BASE_URL}/api/ai-policy")
        policy = get_response.json()
        policy["enabled"] = False
        policy["global_rules"]["allowed_topics"] = ["custom_topic_only"]
        self.session.put(f"{BASE_URL}/api/ai-policy", json=policy)
        
        # Reset to defaults
        reset_response = self.session.post(f"{BASE_URL}/api/ai-policy/reset")
        assert reset_response.status_code == 200
        
        # Verify defaults are restored
        verify_response = self.session.get(f"{BASE_URL}/api/ai-policy")
        reset_policy = verify_response.json()
        
        # Check that enabled is True (default)
        assert reset_policy["enabled"] is True, "enabled should be True after reset"
        
        # Check that default topics are restored
        default_topics = ["apple_products", "apple_repairs", "it_products", "it_services"]
        for topic in default_topics:
            assert topic in reset_policy["global_rules"]["allowed_topics"], f"Default topic '{topic}' should be restored"
    
    def test_reset_ai_policy_sets_last_updated(self):
        """POST /api/ai-policy/reset should set last_updated"""
        reset_response = self.session.post(f"{BASE_URL}/api/ai-policy/reset")
        assert reset_response.status_code == 200
        
        verify_response = self.session.get(f"{BASE_URL}/api/ai-policy")
        policy = verify_response.json()
        
        assert "last_updated" in policy, "last_updated should be set after reset"
        assert policy["last_updated"] is not None, "last_updated should not be None"
    
    def test_reset_ai_policy_requires_auth(self):
        """POST /api/ai-policy/reset should require authentication"""
        no_auth_session = requests.Session()
        response = no_auth_session.post(f"{BASE_URL}/api/ai-policy/reset")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
    
    # ============== Section Update Tests ==============
    
    def test_put_ai_policy_section_global_rules(self):
        """PUT /api/ai-policy/section/global_rules should update only global_rules"""
        new_global_rules = {
            "allowed_topics": ["test_topic_1", "test_topic_2"],
            "disallowed_behavior": ["test_behavior"],
            "scope_message": "Test scope message"
        }
        
        response = self.session.put(f"{BASE_URL}/api/ai-policy/section/global_rules", json=new_global_rules)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify
        verify_response = self.session.get(f"{BASE_URL}/api/ai-policy")
        policy = verify_response.json()
        assert policy["global_rules"]["scope_message"] == "Test scope message"
        
        # Reset to defaults
        self.session.post(f"{BASE_URL}/api/ai-policy/reset")
    
    def test_put_ai_policy_section_invalid_section(self):
        """PUT /api/ai-policy/section/{invalid} should return 400"""
        response = self.session.put(f"{BASE_URL}/api/ai-policy/section/invalid_section", json={})
        assert response.status_code == 400, f"Expected 400 for invalid section, got {response.status_code}"
    
    # ============== State Update Tests ==============
    
    def test_put_ai_policy_state_greeting(self):
        """PUT /api/ai-policy/state/GREETING should update GREETING state"""
        new_greeting_state = {
            "enabled": True,
            "triggers": ["hi", "hello", "test_trigger"],
            "response_template": "Test greeting response"
        }
        
        response = self.session.put(f"{BASE_URL}/api/ai-policy/state/GREETING", json=new_greeting_state)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify
        verify_response = self.session.get(f"{BASE_URL}/api/ai-policy")
        policy = verify_response.json()
        assert "test_trigger" in policy["states"]["GREETING"]["triggers"]
        
        # Reset to defaults
        self.session.post(f"{BASE_URL}/api/ai-policy/reset")
    
    def test_put_ai_policy_state_invalid_state(self):
        """PUT /api/ai-policy/state/{invalid} should return 400"""
        response = self.session.put(f"{BASE_URL}/api/ai-policy/state/INVALID_STATE", json={})
        assert response.status_code == 400, f"Expected 400 for invalid state, got {response.status_code}"
    
    def test_put_ai_policy_state_case_insensitive(self):
        """PUT /api/ai-policy/state/greeting should work (case insensitive)"""
        new_state = {"enabled": True, "triggers": ["hi"]}
        response = self.session.put(f"{BASE_URL}/api/ai-policy/state/greeting", json=new_state)
        assert response.status_code == 200, "State update should be case insensitive"
        
        # Reset
        self.session.post(f"{BASE_URL}/api/ai-policy/reset")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
