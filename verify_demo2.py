import requests
import json
import sys
import time
import subprocess
import os

API_URL = "http://localhost:8000/quiz"
DEMO2_URL = "https://tds-llm-analysis.s-anand.net/demo2"

def verify_demo2():
    print(f"Verifying compatibility with {DEMO2_URL}...")
    
    # Check if server is running
    try:
        requests.get("http://localhost:8000/health", timeout=2)
    except requests.exceptions.ConnectionError:
        print("Server is not running. Starting it now...")
        # Start server in background
        subprocess.Popen([sys.executable, "-m", "uvicorn", "app:app", "--port", "8000"], 
                         cwd=os.getcwd(),
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
        time.sleep(5) # Wait for server to start

    payload = {
        "email": "23f2005433@ds.study.iitm.ac.in",
        "secret": "iamtc",
        "url": DEMO2_URL
    }
    
    try:
        print("Sending request to quiz endpoint...")
        start_time = time.time()
        response = requests.post(API_URL, json=payload, timeout=180) # 3 min timeout
        duration = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Time taken: {duration:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print("Success! Response:")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"Failed with status {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = verify_demo2()
    sys.exit(0 if success else 1)
