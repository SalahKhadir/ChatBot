#!/usr/bin/env python3
"""
Quick test script to verify API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_public_chat():
    """Test public chat endpoint"""
    print("🔍 Testing public chat...")
    try:
        response = requests.post(f"{BASE_URL}/chat/public", data={"message": "Hello!"})
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Public chat works: {response.json()['response'][:50]}...")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_auth_register():
    """Test user registration"""
    print("\n🔍 Testing user registration...")
    user_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Registration works: {response.json()}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_auth_login():
    """Test user login"""
    print("\n🔍 Testing user login...")
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login works: Token starts with {data['access_token'][:20]}...")
            return data['access_token']
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    return None

def test_health():
    """Test health endpoint"""
    print("\n🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Health check: {response.json()}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_authenticated_endpoint():
    """Test authenticated endpoint with token"""
    print("\n🔍 Testing authenticated endpoint...")
    
    # First login to get a token
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    try:
        login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        token = login_response.json()['access_token']
        print(f"✅ Got token: {token[:20]}...")
        
        # Test authenticated endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Authenticated endpoint works: {response.json()}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    print("🤖 ChatBot API Quick Test")
    print("=" * 40)
    
    test_health()
    test_public_chat()
    test_auth_register()
    test_auth_login()
    test_authenticated_endpoint()
    
    print("\n🎉 Tests completed!")

if __name__ == "__main__":
    main()
