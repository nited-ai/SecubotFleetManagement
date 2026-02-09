"""
Test Script 4: Mode Switching Sequence

Tests the complete mode switching flow needed for Pose Mode exit:
  AI mode → Euler (breaks AI mode) → Motion Switcher back to AI → FreeWalk

This addresses Concern #3: Clarify the relationship between "AI mode" 
(Motion Switcher parameter) and "FreeWalk" (API 1045).

What to observe:
1. After Euler API, what mode does Motion Switcher report?
2. Can we switch back to AI mode via Motion Switcher after using Euler?
3. After switching back to AI mode, does FreeWalk (1045) work?
4. After the full sequence, does WASD movement work via WirelessController?
5. How long does the mode switch take? Is 5 seconds enough?

Usage: python test_mode_switching.py
Press Ctrl+C to exit at any time.
"""
import asyncio
import logging
import json
import sys
import time

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


async def test_movement(conn, label, duration=3):
    """Test if movement commands work by sending forward velocity."""
    print(f"  [{label}] Sending forward movement (ly=0.3) for {duration}s...")
    print(f"  OBSERVE: Does the robot move forward?")
    for _ in range(int(duration / 0.05)):
        conn.datachannel.pub_sub.publish_without_callback(
            RTC_TOPIC["WIRELESS_CONTROLLER"],
            {"lx": 0.0, "ly": 0.3, "rx": 0.0, "ry": 0.0, "keys": 0}
        )
        await asyncio.sleep(0.05)
    # Stop
    conn.datachannel.pub_sub.publish_without_callback(
        RTC_TOPIC["WIRELESS_CONTROLLER"],
        {"lx": 0.0, "ly": 0.0, "rx": 0.0, "ry": 0.0, "keys": 0}
    )
    await asyncio.sleep(1)


async def main():
    try:
        conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.8.181")
        await conn.connect()
        print("✅ Connected to robot\n")

        # Step 1: Ensure we're in AI mode + FreeWalk (starting state)
        print("=" * 60)
        print("STEP 1: Ensure robot is in AI mode + FreeWalk")
        print("=" * 60)
        mode = await get_current_mode(conn)
        if mode != "ai":
            print("  Switching to AI mode...")
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
        await get_current_mode(conn)

        # Step 2: Verify movement works in AI mode
        print("\n" + "=" * 60)
        print("STEP 2: Verify movement works in AI mode")
        print("=" * 60)
        await test_movement(conn, "AI mode - before Euler")

        # Step 3: Use Euler API (simulating Pose Mode)
        print("\n" + "=" * 60)
        print("STEP 3: Send Euler (1007) - this should break AI mode")
        print("=" * 60)
        await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {
                "api_id": SPORT_CMD["Euler"],
                "parameter": {"roll": 0.0, "pitch": 0.0, "yaw": 0.3}
            }
        )
        await asyncio.sleep(2)
        print("  Mode after Euler:")
        await get_current_mode(conn)

        # Step 4: Test movement after Euler (should fail)
        print("\n" + "=" * 60)
        print("STEP 4: Test movement AFTER Euler (expected: NOT working)")
        print("=" * 60)
        await test_movement(conn, "After Euler - movement broken?")

        # Step 5: Reset Euler to neutral
        print("\n" + "=" * 60)
        print("STEP 5: Reset Euler to (0,0,0)")
        print("=" * 60)
        await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {
                "api_id": SPORT_CMD["Euler"],
                "parameter": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0}
            }
        )
        await asyncio.sleep(1)

        # Step 6: EXIT SEQUENCE - Switch back to AI mode via Motion Switcher
        print("\n" + "=" * 60)
        print("STEP 6: EXIT SEQUENCE - Switch back to AI mode")
        print("  Sending Motion Switcher → AI mode")
        print("=" * 60)
        start = time.time()
        await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["MOTION_SWITCHER"],
            {"api_id": 1002, "parameter": {"name": "ai"}}
        )
        print(f"  Waiting 5 seconds for mode switch stabilization...")
        await asyncio.sleep(5)
        elapsed = time.time() - start
        print(f"  Elapsed: {elapsed:.1f}s")
        await get_current_mode(conn)

        # Step 7: Send FreeWalk to re-enter Agile Mode
        print("\n" + "=" * 60)
        print("STEP 7: Send FreeWalk (1045) to re-enter Agile Mode")
        print("=" * 60)
        await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {"api_id": SPORT_CMD["FreeWalk"]}
        )
        await asyncio.sleep(2)
        await get_current_mode(conn)

        # Step 8: Test movement after full exit sequence
        print("\n" + "=" * 60)
        print("STEP 8: Test movement AFTER exit sequence")
        print("  CRITICAL: Does movement work again?")
        print("=" * 60)
        await test_movement(conn, "After exit sequence - movement restored?")

        # Summary
        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)
        print("Key questions answered:")
        print("  1. Does Euler break AI mode movement? (Step 4)")
        print("  2. Does Motion Switcher → AI restore it? (Step 6-7)")
        print("  3. Does movement work after full sequence? (Step 8)")
        print("\nPress Ctrl+C to exit")
        await asyncio.sleep(3600)

    except ValueError as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        sys.exit(0)

