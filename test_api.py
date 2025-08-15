#!/usr/bin/env python3
"""
Simple TRMNL API test script
Run this to verify your API credentials work before using the Home Assistant integration
"""

import asyncio
import aiohttp
import sys

# TRMNL API configuration
API_BASE_URL = "https://usetrmnl.com"
API_VERSION = "v1"

async def test_trmnl_api(device_ip: str, api_key: str, device_id: str):
    """Test TRMNL API connection."""
    print(f"🔍 Testing TRMNL API connection...")
    print(f"   Device IP: {device_ip}")
    print(f"   Device ID: {device_id}")
    print(f"   API Key: {api_key[:8]}...{api_key[-8:] if len(api_key) > 16 else '***'}")
    print()
    
    headers = {
        "ID": device_id,
        "Access-Token": api_key,
    }
    
    # Test 1: Get device info
    print("📱 Test 1: Getting device info...")
    try:
        async with aiohttp.ClientSession() as session:
            url = f"http://{device_ip}/api/display"
            async with session.get(url, headers=headers) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Success! Device name: {data.get('name', 'Unknown')}")
                    print(f"   Device model: {data.get('model', 'Unknown')}")
                    print(f"   Firmware: {data.get('firmware_version', 'Unknown')}")
                else:
                    print(f"   ❌ Failed with status {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 2: Get device status
    print("📊 Test 2: Getting device status...")
    try:
        async with aiohttp.ClientSession() as session:
            url = f"http://{device_ip}/api/display"
            async with session.get(url, headers=headers) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Success! Device state: {data.get('state', 'Unknown')}")
                    print(f"   Last seen: {data.get('last_seen', 'Unknown')}")
                else:
                    print(f"   ❌ Failed with status {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 3: List devices (to verify API key works)
    print("🔑 Test 3: Verifying API key with devices list...")
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_BASE_URL}/{API_VERSION}/devices"
            async with session.get(url, headers=headers) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Success! Found {len(data)} device(s)")
                    for device in data:
                        print(f"   - {device.get('name', 'Unknown')} (ID: {device.get('id', 'Unknown')})")
                else:
                    print(f"   ❌ Failed with status {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    """Main function."""
    print("🚀 TRMNL API Connection Test")
    print("=" * 40)
    print()
    
    # Get credentials from user
    device_ip = input("Enter your TRMNL device IP address: ").strip()
    api_key = input("Enter your TRMNL API key: ").strip()
    device_id = input("Enter your TRMNL Device ID: ").strip()
    
    if not device_ip or not api_key or not device_id:
        print("❌ Device IP, API key, and Device ID are all required!")
        sys.exit(1)
    
    print()
    
    # Run the test
    asyncio.run(test_trmnl_api(device_ip, api_key, device_id))
    
    print()
    print("🏁 Test completed!")
    print()
    print("If all tests pass, your credentials should work in Home Assistant.")
    print("If tests fail, check your API key and device ID.")

if __name__ == "__main__":
    main()
