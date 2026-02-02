"""
Test suite for Unanswered Questions and Escalation Code features
- GET /api/unanswered-questions - List unanswered questions with escalation_code field
- PUT /api/unanswered-questions/{id}/relevance - Mark question as relevant/irrelevant
- POST /api/unanswered-questions/{id}/add-kb-article - Create and link KB article
- POST /api/unanswered-questions/{id}/link-kb-article/{kb_id} - Link existing KB article
- Escalation code generation (ESC01, ESC02 format)
- parse_escalation_code_from_message function
"""

import pytest
import requests
import os
import sys

# Add backend to path for importing server functions
sys.path.insert(0, '/app/backend')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthentication:
    """Test login functionality"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "user" in data, "User not in response"
        assert data["user"]["email"] == "test@test.com"
        print(f"SUCCESS: Login returned token and user info")
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@test.com",
            "password": "wrongpass"
        })
        assert response.status_code in [401, 400], f"Expected 401/400, got {response.status_code}"
        print(f"SUCCESS: Invalid login rejected with status {response.status_code}")


class TestUnansweredQuestionsAPI:
    """Test Unanswered Questions API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_get_unanswered_questions_returns_list(self):
        """Test GET /api/unanswered-questions returns list"""
        response = requests.get(
            f"{BASE_URL}/api/unanswered-questions",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: GET /api/unanswered-questions returned {len(data)} questions")
        return data
    
    def test_unanswered_questions_have_escalation_code_field(self):
        """Test that questions have escalation_code field"""
        response = requests.get(
            f"{BASE_URL}/api/unanswered-questions?status=all",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            question = data[0]
            assert "escalation_code" in question, "escalation_code field missing"
            assert "id" in question, "id field missing"
            assert "question" in question, "question field missing"
            assert "status" in question, "status field missing"
            assert "customer_name" in question, "customer_name field missing"
            print(f"SUCCESS: Question has escalation_code: {question.get('escalation_code')}")
        else:
            print("INFO: No unanswered questions found - skipping field validation")
    
    def test_unanswered_questions_filter_by_status(self):
        """Test filtering by status"""
        # Test pending filter
        response = requests.get(
            f"{BASE_URL}/api/unanswered-questions?status=pending_owner_reply",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        for q in data:
            assert q["status"] == "pending_owner_reply", f"Expected pending_owner_reply, got {q['status']}"
        print(f"SUCCESS: Status filter works - {len(data)} pending questions")
    
    def test_unanswered_questions_filter_by_relevance(self):
        """Test filtering by relevance"""
        response = requests.get(
            f"{BASE_URL}/api/unanswered-questions?status=all&relevance=relevant",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        for q in data:
            assert q.get("relevance") == "relevant", f"Expected relevant, got {q.get('relevance')}"
        print(f"SUCCESS: Relevance filter works - {len(data)} relevant questions")
    
    def test_unanswered_questions_requires_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/unanswered-questions")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"SUCCESS: Endpoint requires auth - returned {response.status_code}")


class TestRelevanceAPI:
    """Test relevance marking API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_mark_relevance_invalid_value(self):
        """Test marking with invalid relevance value"""
        response = requests.put(
            f"{BASE_URL}/api/unanswered-questions/fake-id/relevance?relevance=invalid",
            headers=self.headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"SUCCESS: Invalid relevance value rejected")
    
    def test_mark_relevance_not_found(self):
        """Test marking non-existent question"""
        response = requests.put(
            f"{BASE_URL}/api/unanswered-questions/non-existent-id/relevance?relevance=irrelevant",
            headers=self.headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"SUCCESS: Non-existent question returns 404")


class TestKBArticleAPI:
    """Test KB article creation and linking APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_add_kb_article_not_found(self):
        """Test adding KB article to non-existent question"""
        response = requests.post(
            f"{BASE_URL}/api/unanswered-questions/non-existent-id/add-kb-article?title=Test&content=Test&category=FAQ",
            headers=self.headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"SUCCESS: Non-existent question returns 404 for add-kb-article")
    
    def test_link_kb_article_question_not_found(self):
        """Test linking KB article to non-existent question"""
        response = requests.post(
            f"{BASE_URL}/api/unanswered-questions/non-existent-id/link-kb-article/some-kb-id",
            headers=self.headers
        )
        # Could be 404 for question or KB article
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"SUCCESS: Non-existent question/KB returns 404 for link-kb-article")
    
    def test_get_kb_articles(self):
        """Test GET /api/kb returns list of KB articles"""
        response = requests.get(
            f"{BASE_URL}/api/kb",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: GET /api/kb returned {len(data)} articles")


class TestEscalationCodeParsing:
    """Test escalation code parsing function"""
    
    def test_parse_escalation_code_with_colon(self):
        """Test parsing 'ESC01: answer' format"""
        from server import parse_escalation_code_from_message
        
        code, reply = parse_escalation_code_from_message("ESC01: Here's the answer to your question")
        assert code == "ESC01", f"Expected ESC01, got {code}"
        assert reply == "Here's the answer to your question", f"Reply mismatch: {reply}"
        print(f"SUCCESS: Parsed 'ESC01: answer' format correctly")
    
    def test_parse_escalation_code_with_space(self):
        """Test parsing 'ESC01 answer' format"""
        from server import parse_escalation_code_from_message
        
        code, reply = parse_escalation_code_from_message("ESC02 Yes we have it in stock")
        assert code == "ESC02", f"Expected ESC02, got {code}"
        assert reply == "Yes we have it in stock", f"Reply mismatch: {reply}"
        print(f"SUCCESS: Parsed 'ESC02 answer' format correctly")
    
    def test_parse_escalation_code_lowercase(self):
        """Test parsing lowercase 'esc01: answer' format"""
        from server import parse_escalation_code_from_message
        
        code, reply = parse_escalation_code_from_message("esc03: The price is 45000")
        assert code == "ESC03", f"Expected ESC03, got {code}"
        assert reply == "The price is 45000", f"Reply mismatch: {reply}"
        print(f"SUCCESS: Parsed lowercase 'esc03: answer' format correctly")
    
    def test_parse_no_escalation_code(self):
        """Test parsing message without escalation code"""
        from server import parse_escalation_code_from_message
        
        code, reply = parse_escalation_code_from_message("Just a regular message")
        assert code is None, f"Expected None, got {code}"
        assert reply == "Just a regular message", f"Reply should be original message"
        print(f"SUCCESS: Message without code returns (None, original_message)")
    
    def test_parse_escalation_code_double_digit(self):
        """Test parsing double digit codes like ESC12"""
        from server import parse_escalation_code_from_message
        
        code, reply = parse_escalation_code_from_message("ESC12: Answer for escalation 12")
        assert code == "ESC12", f"Expected ESC12, got {code}"
        print(f"SUCCESS: Parsed double digit code ESC12 correctly")


class TestEscalationsAPI:
    """Test escalations API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            pytest.skip("Authentication failed")
    
    def test_get_escalations(self):
        """Test GET /api/escalations returns list"""
        response = requests.get(
            f"{BASE_URL}/api/escalations",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: GET /api/escalations returned {len(data)} escalations")
    
    def test_get_pending_sla_escalations(self):
        """Test GET /api/escalations/pending-sla returns SLA info"""
        response = requests.get(
            f"{BASE_URL}/api/escalations/pending-sla",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: GET /api/escalations/pending-sla returned {len(data)} pending escalations")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
