"""
Test Script 2: Pose API (1028)

Tests Option A for Pose Mode - the standalone Pose command.

What to observe:
1. What does Pose (1028) do? Does it toggle between walk/pose mode?
2. Does it accept parameters? If so, what format?
3. After Pose (1028), can we control orientation with Euler (1007)?
4. After Pose (1028), can we still send Move commands?
5. Can we exit Pose mode by sending Pose (1028) again (toggle)?
6. What motion mode does the robot report after Pose (1028)?

Usage: python test_pose_api_1028.py
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

        # Step 2: Send Pose API (1028) - no parameters
        print("\n" + "=" * 60)
        print("STEP 2: Send Pose API (1028) - no parameters")
        print("  OBSERVE: What happens? Does robot change stance?")
        print("=" * 60)
        response = await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {"api_id": SPORT_CMD["Pose"]}
        )
        status_code = response.get('data', {}).get('header', {}).get('status', {}).get('code', 'N/A')
        print(f"  Response status code: {status_code}")
        print(f"  Full response: {json.dumps(response, indent=2)}")
        await asyncio.sleep(3)
        await get_current_mode(conn)

        # Step 3: Try Euler while in Pose mode
        print("\n" + "=" * 60)
        print("STEP 3: Send Euler (1007) while in Pose mode")
        print("  OBSERVE: Does orientation control work?")
        print("=" * 60)
        response = await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {
                "api_id": SPORT_CMD["Euler"],
                "parameter": {"roll": 0.0, "pitch": 0.0, "yaw": 0.3}
            }
        )
        status_code = response.get('data', {}).get('header', {}).get('status', {}).get('code', 'N/A')
        print(f"  Response status code: {status_code}")
        await asyncio.sleep(3)

        # Step 4: Reset Euler
        print("\n" + "=" * 60)
        print("STEP 4: Reset Euler to (0,0,0)")
        print("=" * 60)
        await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {
                "api_id": SPORT_CMD["Euler"],
                "parameter": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0}
            }
        )
        await asyncio.sleep(2)

        # Step 5: Send Pose (1028) again to toggle back
        print("\n" + "=" * 60)
        print("STEP 5: Send Pose API (1028) again (toggle back)")
        print("  OBSERVE: Does it return to walk mode?")
        print("=" * 60)
        response = await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {"api_id": SPORT_CMD["Pose"]}
        )
        status_code = response.get('data', {}).get('header', {}).get('status', {}).get('code', 'N/A')
        print(f"  Response status code: {status_code}")
        await asyncio.sleep(3)
        await get_current_mode(conn)

        # Step 6: Test Pose (1028) with parameter (in case it accepts orientation)
        print("\n" + "=" * 60)
        print("STEP 6: Send Pose (1028) WITH parameter")
        print("  Testing if it accepts orientation parameters")
        print("=" * 60)
        response = await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {
                "api_id": SPORT_CMD["Pose"],
                "parameter": {"roll": 0.0, "pitch": 0.2, "yaw": 0.3}
            }
        )
        status_code = response.get('data', {}).get('header', {}).get('status', {}).get('code', 'N/A')
        print(f"  Response status code: {status_code}")
        print(f"  Full response: {json.dumps(response, indent=2)}")
        await asyncio.sleep(3)

        # Step 7: Final mode check
        print("\n" + "=" * 60)
        print("STEP 7: Final mode check")
        print("=" * 60)
        final_mode = await get_current_mode(conn)
        print(f"\n  Mode journey: {initial_mode} → ... → {final_mode}")

        # Keep alive
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

