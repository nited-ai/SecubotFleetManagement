"""
Test Script 1: BalanceStand (1002) + Euler (1007)

Tests Option B for Pose Mode - using BalanceStand to stabilize, then Euler to control orientation.

What to observe:
1. Does BalanceStand make the robot stand still and stable?
2. Does Euler (1007) change the robot's body orientation (roll, pitch, yaw)?
3. What are the safe angle ranges before the robot becomes unstable?
4. After using Euler, can we still send Move commands? (Expected: NO - it breaks AI mode)
5. Does resetting Euler to (0,0,0) return the robot to neutral stance?

Usage: python test_balance_stand_euler.py
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


async def send_euler(conn, roll, pitch, yaw):
    """Send Euler command and print response."""
    print(f"  Sending Euler: roll={roll}, pitch={pitch}, yaw={yaw}")
    response = await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"],
        {
            "api_id": SPORT_CMD["Euler"],
            "parameter": {"roll": roll, "pitch": pitch, "yaw": yaw}
        }
    )
    status_code = response.get('data', {}).get('header', {}).get('status', {}).get('code', 'N/A')
    print(f"  Response status code: {status_code}")
    return response


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

        # Step 2: Send BalanceStand
        print("\n" + "=" * 60)
        print("STEP 2: Send BalanceStand (1002)")
        print("  OBSERVE: Robot should stand still and stable")
        print("=" * 60)
        await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {"api_id": SPORT_CMD["BalanceStand"]}
        )
        await asyncio.sleep(2)
        await get_current_mode(conn)

        # Step 3: Test Euler with small yaw
        print("\n" + "=" * 60)
        print("STEP 3: Euler - small yaw (0.3 rad ≈ 17°)")
        print("  OBSERVE: Robot body should rotate right")
        print("=" * 60)
        await send_euler(conn, 0.0, 0.0, 0.3)
        await asyncio.sleep(3)
        await get_current_mode(conn)

        # Step 4: Test Euler with small pitch
        print("\n" + "=" * 60)
        print("STEP 4: Euler - small pitch (0.2 rad ≈ 11°)")
        print("  OBSERVE: Robot body should tilt forward")
        print("=" * 60)
        await send_euler(conn, 0.0, 0.2, 0.0)
        await asyncio.sleep(3)

        # Step 5: Test Euler with small roll
        print("\n" + "=" * 60)
        print("STEP 5: Euler - small roll (0.2 rad ≈ 11°)")
        print("  OBSERVE: Robot body should lean right")
        print("=" * 60)
        await send_euler(conn, 0.2, 0.0, 0.0)
        await asyncio.sleep(3)

        # Step 6: Combined angles
        print("\n" + "=" * 60)
        print("STEP 6: Euler - combined (roll=0.15, pitch=0.15, yaw=0.2)")
        print("  OBSERVE: Robot should tilt, lean, and rotate simultaneously")
        print("=" * 60)
        await send_euler(conn, 0.15, 0.15, 0.2)
        await asyncio.sleep(3)

        # Step 7: Reset to neutral
        print("\n" + "=" * 60)
        print("STEP 7: Euler - reset to (0, 0, 0)")
        print("  OBSERVE: Robot should return to neutral stance")
        print("=" * 60)
        await send_euler(conn, 0.0, 0.0, 0.0)
        await asyncio.sleep(2)

        # Step 8: Check mode after Euler usage
        print("\n" + "=" * 60)
        print("STEP 8: Check mode after Euler usage")
        print("  EXPECTED: Mode may have changed from AI to something else")
        print("=" * 60)
        post_euler_mode = await get_current_mode(conn)
        print(f"\n  Mode changed: {initial_mode} → {post_euler_mode}")

        # Keep alive for observation
        print("\n" + "=" * 60)
        print("TEST COMPLETE - Robot staying connected for observation")
        print("Press Ctrl+C to exit")
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

