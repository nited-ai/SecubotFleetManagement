"""
Test Script 3: BodyHeight API (1013)

Tests body height control to determine the correct API and parameter format.

What to observe:
1. Does BodyHeight (1013) with {"height": value} work?
2. What range of height values are valid? (testing -0.18, 0.0, 0.15 and others)
3. Does BodyHeight work in AI mode? (existing comment says it may not)
4. Does BodyHeight work in normal mode?
5. Does BodyHeight work after BalanceStand?
6. Is there an alternative approach via WirelessController ry?

Current implementation in control.py uses:
  height_values = [-0.18, 0.0, 0.15]  (low, middle, high)
  parameter format: {"height": height_value}
  
The wireless controller's left stick up/down (ly axis) controls height on the remote.
Question: Does WirelessController 'ry' control height? Need to test.

Usage: python test_body_height.py
Press Ctrl+C to exit at any time.
"""
import asyncio
import logging
import json
import sys

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod
from unitree_webrtc_connect.constants import RTC_TOPIC, SPORT_CMD

logging.basicConfig(level=logging.WARNING)


async def get_current_mode(conn):
    """Get and display current motion mode."""
    response = await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["MOTION_SWITCHER"],
        {"api_id": 1001}
    )
    if response and 'data' in response:
        data = json.loads(response['data']['data'])
        mode = data.get('name', 'unknown')
        print(f"  Current motion mode: {mode}")
        return mode
    return "unknown"


async def send_body_height(conn, height_value, label=""):
    """Send BodyHeight command and print response."""
    print(f"  Sending BodyHeight: height={height_value} {label}")
    try:
        response = await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {
                "api_id": SPORT_CMD["BodyHeight"],
                "parameter": {"height": height_value}
            }
        )
        status_code = response.get('data', {}).get('header', {}).get('status', {}).get('code', 'N/A')
        print(f"  Response status code: {status_code}")
        return response
    except Exception as e:
        print(f"  Error: {e}")
        return None


async def main():
    try:
        conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.8.181")
        await conn.connect()
        print("✅ Connected to robot\n")

        # Step 1: Check initial mode
        print("=" * 60)
        print("STEP 1: Check initial mode")
        print("=" * 60)
        initial_mode = await get_current_mode(conn)
        await asyncio.sleep(1)

        # Step 2: Test BodyHeight in current mode (likely AI)
        print("\n" + "=" * 60)
        print(f"STEP 2: Test BodyHeight in current mode ({initial_mode})")
        print("  OBSERVE: Does the robot change height?")
        print("=" * 60)

        await send_body_height(conn, -0.18, "(low)")
        await asyncio.sleep(3)

        await send_body_height(conn, 0.0, "(middle/default)")
        await asyncio.sleep(3)

        await send_body_height(conn, 0.15, "(high)")
        await asyncio.sleep(3)

        await send_body_height(conn, 0.0, "(reset to middle)")
        await asyncio.sleep(2)

        # Step 3: Test BodyHeight after BalanceStand (normal sport mode context)
        print("\n" + "=" * 60)
        print("STEP 3: Send BalanceStand first, then test BodyHeight")
        print("  OBSERVE: Does BodyHeight work better after BalanceStand?")
        print("=" * 60)
        await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {"api_id": SPORT_CMD["BalanceStand"]}
        )
        await asyncio.sleep(2)

        await send_body_height(conn, -0.18, "(low)")
        await asyncio.sleep(3)

        await send_body_height(conn, 0.15, "(high)")
        await asyncio.sleep(3)

        await send_body_height(conn, 0.0, "(reset to middle)")
        await asyncio.sleep(2)

        # Step 4: Test extended height range
        print("\n" + "=" * 60)
        print("STEP 4: Test extended height range")
        print("  OBSERVE: What are the actual min/max values?")
        print("=" * 60)
        for h in [-0.25, -0.20, -0.15, -0.10, -0.05, 0.0, 0.05, 0.10, 0.15, 0.20, 0.25]:
            await send_body_height(conn, h, f"(testing range)")
            await asyncio.sleep(2)

        # Step 5: Test WirelessController ry for height control
        print("\n" + "=" * 60)
        print("STEP 5: Test WirelessController ry for height")
        print("  OBSERVE: Does ry control body height?")
        print("  (On wireless remote, left stick Y controls height)")
        print("=" * 60)

        # First go back to AI mode + FreeWalk
        print("  Returning to AI mode for WirelessController test...")
        await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["MOTION_SWITCHER"],
            {"api_id": 1002, "parameter": {"name": "ai"}}
        )
        await asyncio.sleep(5)
        await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {"api_id": SPORT_CMD["FreeWalk"]}
        )
        await asyncio.sleep(2)

        # Test ry positive (should raise?)
        print("  Sending WirelessController ry=0.5 (positive)")
        conn.datachannel.pub_sub.publish_without_callback(
            RTC_TOPIC["WIRELESS_CONTROLLER"],
            {"lx": 0.0, "ly": 0.0, "rx": 0.0, "ry": 0.5, "keys": 0}
        )
        await asyncio.sleep(3)

        # Test ry negative (should lower?)
        print("  Sending WirelessController ry=-0.5 (negative)")
        conn.datachannel.pub_sub.publish_without_callback(
            RTC_TOPIC["WIRELESS_CONTROLLER"],
            {"lx": 0.0, "ly": 0.0, "rx": 0.0, "ry": -0.5, "keys": 0}
        )
        await asyncio.sleep(3)

        # Reset
        print("  Sending WirelessController ry=0.0 (reset)")
        conn.datachannel.pub_sub.publish_without_callback(
            RTC_TOPIC["WIRELESS_CONTROLLER"],
            {"lx": 0.0, "ly": 0.0, "rx": 0.0, "ry": 0.0, "keys": 0}
        )
        await asyncio.sleep(1)

        # Final check
        print("\n" + "=" * 60)
        print("TEST COMPLETE - Press Ctrl+C to exit")
        print("=" * 60)
        await asyncio.sleep(3600)

    except ValueError as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        sys.exit(0)

