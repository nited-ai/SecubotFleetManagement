"""
Debug script to subscribe to various robot topics and log their messages.
This helps understand message formats and discover correct obstacle avoidance commands.

Usage:
    python scripts/debug_topic_subscriptions.py
"""

import asyncio
import logging
import json
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod
from unitree_webrtc_connect.constants import RTC_TOPIC

# Enable detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Topics to monitor
TOPICS_TO_MONITOR = [
    # Obstacle avoidance related
    ("OBSTACLES_AVOID", "rt/api/obstacles_avoid/request"),
    ("OBSTACLES_AVOID_RESPONSE", "rt/api/obstacles_avoid/response"),
    
    # LIDAR related
    ("ULIDAR_STATE", "rt/utlidar/lidar_state"),
    ("ULIDAR_SWITCH", "rt/utlidar/switch"),
    
    # Sport mode state
    ("SPORT_MOD_STATE", "rt/sportmodestate"),
    ("LF_SPORT_MOD_STATE", "rt/lf/sportmodestate"),
    
    # Service state (might contain obstacle avoidance info)
    ("SERVICE_STATE", "rt/servicestate"),
    
    # Try potential MCF_MOD topic (might not exist)
    ("MCF_MOD_REQUEST", "rt/api/mcf/request"),
    ("MCF_MOD_RESPONSE", "rt/api/mcf/response"),
]


def create_callback(topic_name):
    """Create a callback function for a specific topic."""
    def callback(message):
        print("\n" + "=" * 80)
        print(f"📡 TOPIC: {topic_name}")
        print("=" * 80)
        try:
            # Pretty print the message
            print(json.dumps(message, indent=2, ensure_ascii=False))
        except:
            # If JSON formatting fails, just print raw
            print(message)
        print("=" * 80 + "\n")
    return callback


async def main():
    try:
        # Connect to robot (adjust IP as needed)
        print("Connecting to robot...")
        conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.8.181")
        await conn.connect()
        print("✅ Connected to robot\n")
        
        # Disable traffic saving to receive all data
        await conn.datachannel.disableTrafficSaving(True)
        print("✅ Traffic saving disabled\n")
        
        # Subscribe to all topics
        print("Subscribing to topics...")
        for topic_name, topic_path in TOPICS_TO_MONITOR:
            try:
                conn.datachannel.pub_sub.subscribe(topic_path, create_callback(topic_name))
                print(f"  ✓ Subscribed to: {topic_name} ({topic_path})")
            except Exception as e:
                print(f"  ✗ Failed to subscribe to {topic_name}: {e}")
        
        print("\n" + "=" * 80)
        print("🎧 LISTENING FOR MESSAGES (Press Ctrl+C to stop)")
        print("=" * 80)
        print("\nNow try toggling obstacle avoidance in the web interface...")
        print("Watch for messages on OBSTACLES_AVOID, SPORT_MOD_STATE, or SERVICE_STATE topics\n")
        
        # Keep running to receive messages
        await asyncio.sleep(3600)  # Run for 1 hour
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
    except Exception as e:
        logging.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

