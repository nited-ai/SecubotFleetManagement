"""
Simple diagnostic script to test connection to Unitree Go2 robot.
This will help identify connection issues.
"""

import asyncio
import logging
import sys
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

# Enable detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_connection(ip_address):
    """Test connection to the robot"""
    print("=" * 60)
    print("Unitree Go2 Connection Test")
    print("=" * 60)
    print(f"\nAttempting to connect to robot at IP: {ip_address}")
    print("Please wait...\n")
    
    try:
        # Create connection
        print("Step 1: Creating WebRTC connection object...")
        conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip=ip_address)
        
        # Attempt to connect
        print("Step 2: Initiating connection to robot...")
        print("(This may take 10-30 seconds)")
        await conn.connect()
        
        print("\n✅ SUCCESS! Connected to robot successfully!")
        print("\nConnection details:")
        print(f"  - IP Address: {ip_address}")
        print(f"  - Connection Method: LocalSTA")
        print(f"  - Status: Connected")
        
        # Try to enable video
        print("\nStep 3: Testing video channel...")
        conn.video.switchVideoChannel(True)
        print("✅ Video channel enabled successfully!")
        
        print("\n" + "=" * 60)
        print("All tests passed! Your robot is ready to use.")
        print("You can now use the web interface to connect.")
        print("=" * 60)
        
        # Disconnect
        print("\nDisconnecting...")
        await conn.disconnect()
        print("✅ Disconnected successfully")
        
        return True
        
    except asyncio.TimeoutError:
        print("\n❌ ERROR: Connection timeout")
        print("\nPossible causes:")
        print("  1. Robot is not powered on")
        print("  2. IP address is incorrect")
        print("  3. Robot and computer are not on the same network")
        print("  4. Firewall is blocking the connection")
        return False
        
    except ConnectionRefusedError:
        print("\n❌ ERROR: Connection refused")
        print("\nPossible causes:")
        print("  1. Robot is not responding on this IP address")
        print("  2. WebRTC service is not running on the robot")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}")
        print(f"Details: {str(e)}")
        
        error_str = str(e).lower()
        print("\nPossible causes:")
        
        if "reject" in error_str:
            print("  - Robot is already connected to another WebRTC client")
            print("  - Close the Unitree mobile app and try again")
        elif "unreachable" in error_str or "timeout" in error_str:
            print("  - Cannot reach the robot at this IP address")
            print("  - Check if robot and computer are on the same network")
            print("  - Verify the IP address is correct")
        else:
            print("  - Unknown error occurred")
            print("  - Check the error details above")
        
        return False

def validate_ip(ip):
    """Validate IP address format"""
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False

def main():
    print("\n")
    
    # Get IP from command line or prompt user
    if len(sys.argv) > 1:
        ip_address = sys.argv[1]
    else:
        print("Enter the robot's IP address")
        print("(or press Enter to use default: 192.168.8.181)")
        ip_input = input("IP Address: ").strip()
        ip_address = ip_input if ip_input else "192.168.8.181"
    
    # Validate IP
    if not validate_ip(ip_address):
        print(f"\n❌ ERROR: Invalid IP address format: {ip_address}")
        print("IP address must be in format: xxx.xxx.xxx.xxx")
        print("where each xxx is a number between 0 and 255")
        print("\nExample: 192.168.8.181")
        sys.exit(1)
    
    # Run the test
    try:
        success = asyncio.run(test_connection(ip_address))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)

if __name__ == "__main__":
    main()

