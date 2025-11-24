"""Test script for the quiz endpoint."""
import requests
import json
import sys

# Configuration
API_URL = "http://localhost:8000/quiz"  # Change to your deployed URL for production
DEMO_URL = "https://tds-llm-analysis.s-anand.net/demo"

def test_valid_request():
    """Test with valid credentials."""
    print("Testing valid request...")
    
    payload = {
        "email": "23f2005433@ds.study.iitm.ac.in",  # Replace with your email
        "secret": "iamtc",      # Replace with your secret
        "url": DEMO_URL
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✓ Valid request test passed")
            return True
        else:
            print("✗ Valid request test failed")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_invalid_json():
    """Test with invalid JSON."""
    print("\nTesting invalid JSON...")
    
    try:
        response = requests.post(
            API_URL,
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 400:
            print("✓ Invalid JSON test passed")
            return True
        else:
            print("✗ Invalid JSON test failed (expected 400)")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_invalid_secret():
    """Test with invalid secret."""
    print("\nTesting invalid secret...")
    
    payload = {
        "email": "your-email@example.com",
        "secret": "wrong-secret",
        "url": DEMO_URL
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 403:
            print("✓ Invalid secret test passed")
            return True
        else:
            print("✗ Invalid secret test failed (expected 403)")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_invalid_email():
    """Test with invalid email."""
    print("\nTesting invalid email...")
    
    payload = {
        "email": "wrong@example.com",
        "secret": "your-secret-string",
        "url": DEMO_URL
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 403:
            print("✓ Invalid email test passed")
            return True
        else:
            print("✗ Invalid email test failed (expected 403)")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_health_endpoint():
    """Test health check endpoint."""
    print("\nTesting health endpoint...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✓ Health check passed")
            return True
        else:
            print("✗ Health check failed")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("LLM Analysis Quiz - Endpoint Tests")
    print("=" * 60)
    
    # Check if server is running
    try:
        requests.get("http://localhost:8000/", timeout=5)
    except:
        print("✗ Server is not running at http://localhost:8000")
        print("Start the server with: uvicorn app:app --reload")
        sys.exit(1)
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_endpoint()))
    results.append(("Valid Request", test_valid_request()))
    results.append(("Invalid JSON", test_invalid_json()))
    results.append(("Invalid Secret", test_invalid_secret()))
    results.append(("Invalid Email", test_invalid_email()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
