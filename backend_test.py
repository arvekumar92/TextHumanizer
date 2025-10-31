import requests
import sys
import json
from datetime import datetime

class TextHumanizerAPITester:
    def __init__(self, base_url="https://grammar-fix-9.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "status": "PASS" if success else "FAIL",
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {name}: {details}")
        return success

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}" if endpoint else f"{self.base_url}/api"
        headers = {'Content-Type': 'application/json'}

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    details = f"Status: {response.status_code}, Response: {json.dumps(response_data, indent=2)[:200]}..."
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}..."
            else:
                details = f"Expected {expected_status}, got {response.status_code}. Response: {response.text[:200]}..."

            self.log_test(name, success, details)
            return success, response.json() if success and response.text else {}

        except requests.exceptions.Timeout:
            details = f"Request timed out after {timeout} seconds"
            self.log_test(name, False, details)
            return False, {}
        except Exception as e:
            details = f"Error: {str(e)}"
            self.log_test(name, False, details)
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root Endpoint", "GET", "", 200)

    def test_rephrase_conversational(self):
        """Test rephrase with conversational tone"""
        data = {
            "text": "This is a test sentence that needs rephrasing.",
            "tone": "conversational"
        }
        return self.run_test("Rephrase - Conversational", "POST", "rephrase", 200, data, timeout=60)

    def test_rephrase_formal(self):
        """Test rephrase with formal tone"""
        data = {
            "text": "Hey there! How's it going?",
            "tone": "formal"
        }
        return self.run_test("Rephrase - Formal", "POST", "rephrase", 200, data, timeout=60)

    def test_rephrase_academic(self):
        """Test rephrase with academic tone"""
        data = {
            "text": "This thing is really important for our study.",
            "tone": "academic"
        }
        return self.run_test("Rephrase - Academic", "POST", "rephrase", 200, data, timeout=60)

    def test_rephrase_creative(self):
        """Test rephrase with creative tone"""
        data = {
            "text": "The weather is nice today.",
            "tone": "creative"
        }
        return self.run_test("Rephrase - Creative", "POST", "rephrase", 200, data, timeout=60)

    def test_rephrase_empty_text(self):
        """Test rephrase with empty text"""
        data = {
            "text": "",
            "tone": "conversational"
        }
        success, response = self.run_test("Rephrase - Empty Text", "POST", "rephrase", 422, data)
        return success

    def test_rephrase_invalid_tone(self):
        """Test rephrase with invalid tone"""
        data = {
            "text": "Test text",
            "tone": "invalid_tone"
        }
        success, response = self.run_test("Rephrase - Invalid Tone", "POST", "rephrase", 200, data, timeout=60)
        return success

    def test_save_history(self):
        """Test saving history"""
        data = {
            "original_text": "Test original text",
            "rephrased_text": "Test rephrased text",
            "tone": "conversational"
        }
        success, response = self.run_test("Save History", "POST", "history", 200, data)
        if success and 'id' in response:
            return success, response['id']
        return success, None

    def test_get_history(self):
        """Test getting history"""
        return self.run_test("Get History", "GET", "history", 200)

    def test_delete_history(self, history_id):
        """Test deleting history item"""
        if not history_id:
            self.log_test("Delete History", False, "No history ID provided")
            return False
        
        return self.run_test("Delete History", "DELETE", f"history/{history_id}", 200)

    def test_delete_nonexistent_history(self):
        """Test deleting non-existent history item"""
        fake_id = "non-existent-id-12345"
        return self.run_test("Delete Non-existent History", "DELETE", f"history/{fake_id}", 404)

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting TextHumanizer API Tests")
        print("=" * 50)

        # Test basic connectivity
        success, _ = self.test_root_endpoint()
        if not success:
            print("❌ Root endpoint failed - stopping tests")
            return False

        # Test rephrase functionality with different tones
        self.test_rephrase_conversational()
        self.test_rephrase_formal()
        self.test_rephrase_academic()
        self.test_rephrase_creative()
        
        # Test edge cases
        self.test_rephrase_empty_text()
        self.test_rephrase_invalid_tone()

        # Test history functionality
        success, history_id = self.test_save_history()
        self.test_get_history()
        
        if history_id:
            self.test_delete_history(history_id)
        
        self.test_delete_nonexistent_history()

        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    tester = TextHumanizerAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            'summary': {
                'total_tests': tester.tests_run,
                'passed_tests': tester.tests_passed,
                'success_rate': f"{(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "0%",
                'timestamp': datetime.now().isoformat()
            },
            'detailed_results': tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())