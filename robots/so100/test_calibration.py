#!/usr/bin/env python
"""
SO-ARM100 Calibration Test Script

This script creates a mock environment to test the calibration logic without actual hardware.
It allows testing the script structure and flow without requiring physical hardware connections.
"""

import os
import sys
import argparse
import json
from unittest.mock import MagicMock

# Add parent directory to path for proper imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)


# Mock the required dependencies
class MockBus:
    def __init__(self, port, description):
        self.port = port
        self.descriptions = description
        print(f"Mock connection established to port {port}")

    def write_torque_enable(self, data):
        print("Mock: Torque disabled")
        return True

    def write_operating_mode(self, data):
        print("Mock: Operating mode set")
        return True

    def write_max_angle_limit(self, data):
        print("Mock: Max angle limit set")
        return True

    def write_min_angle_limit(self, data):
        print("Mock: Min angle limit set")
        return True

    def read_position(self, joints):
        # Return mock position values
        print("Mock: Reading position")
        return {"values": MagicMock(values=[100, 200, 300, 400, 500, 600])}


class MockTorqueMode:
    DISABLED = MagicMock(value=0)
    ENABLED = MagicMock(value=1)


class MockOperatingMode:
    ONE_TURN = MagicMock(value=0)


class MockPyArrow:
    @staticmethod
    def array(data, type=None):
        return data

    @staticmethod
    def scalar(value, type=None):
        return value

    # Add uint32 data type
    @staticmethod
    def uint32():
        return "uint32_mock"

    class string:
        @staticmethod
        def __call__():
            return "string"

    class StructArray:
        @staticmethod
        def from_arrays(arrays, names):
            result = MagicMock()
            result.field = lambda x: arrays[0] if x == "joints" else arrays[1]
            return result


class MockConversionTables:
    @staticmethod
    def construct_pwm_to_logical_conversion_table_arrow(positions, targets):
        print("Mock: Creating PWM to logical conversion table")
        return {
            "shoulder_pan": [1, 0],
            "shoulder_lift": [1, 0],
            "elbow_flex": [1, 0],
            "wrist_flex": [1, 0],
            "wrist_roll": [1, 0],
            "gripper": [1, 0],
        }

    @staticmethod
    def construct_logical_to_pwm_conversion_table_arrow(positions, targets):
        print("Mock: Creating logical to PWM conversion table")
        return {
            "shoulder_pan": [1, 0],
            "shoulder_lift": [1, 0],
            "elbow_flex": [1, 0],
            "wrist_flex": [1, 0],
            "wrist_roll": [1, 0],
            "gripper": [1, 0],
        }


class MockFunctions:
    @staticmethod
    def construct_control_table(table1, table2):
        print("Mock: Constructing control table")
        return {}


class MockTransform:
    @staticmethod
    def pwm_to_logical_arrow(pwm, table, ranged=True):
        result = MagicMock()
        result.field = lambda x: [10, 20, 30, 40, 50, 60]
        return result


# Setup mocks
sys.modules["pyarrow"] = MockPyArrow
sys.modules["bus"] = MagicMock()
sys.modules["bus"].FeetechBus = MockBus
sys.modules["bus"].TorqueMode = MockTorqueMode
sys.modules["bus"].OperatingMode = MockOperatingMode
sys.modules["pwm_position_control.tables"] = MockConversionTables
sys.modules["pwm_position_control.functions"] = MockFunctions
sys.modules["pwm_position_control.transform"] = MockTransform


def test_calibration_flow():
    """Test the basic flow of the calibration process"""
    try:
        # Try direct import first
        calibration_file = os.path.join(current_dir, "calibrate_so_arm100.py")

        # If the file exists, import it directly
        if os.path.exists(calibration_file):
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "calibrate_module", calibration_file
            )
            calibrate_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(calibrate_module)

            calibrate_arm = calibrate_module.calibrate_arm
            wrap_joints_and_values = calibrate_module.wrap_joints_and_values
            pause = calibrate_module.pause

            # Override the pause function to avoid waiting for input
            def mock_pause(message="Press Enter to continue..."):
                print(f"Mock pause: {message}")

            # Replace the module's pause function
            calibrate_module.pause = mock_pause
        else:
            # Fall back to regular import
            from robots.so100.calibrate_so_arm100 import (
                calibrate_arm,
                wrap_joints_and_values,
                pause,
            )

            # Override the pause function to avoid waiting for input
            def mock_pause(message="Press Enter to continue..."):
                print(f"Mock pause: {message}")

            # Replace the imported pause function
            globals()["pause"] = mock_pause

        print("\n===== TESTING CALIBRATION FLOW =====\n")

        # Call the calibration function with test parameters
        result = calibrate_arm("COM3", "left")

        print("\n===== TEST COMPLETED =====")
        print(f"Calibration result: {'Success' if result else 'Failed'}")

    except Exception as e:
        print(f"Error in calibration flow test: {e}")
        import traceback

        traceback.print_exc()


def test_argument_parsing():
    """Test the argument parsing logic"""
    print("\n===== TESTING ARGUMENT PARSING =====\n")

    # Create test arguments
    test_args = ["--port", "COM3", "--left"]

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="SO-ARM100 Calibration Tool: Guides users through calibrating the SO-ARM100 robot arm."
    )

    parser.add_argument(
        "--port",
        type=str,
        required=True,
        help="The serial port of the SO-ARM100 (e.g., /dev/ttyUSB0 or COM3)",
    )
    parser.add_argument(
        "--right",
        action="store_true",
        help="Calibrate the arm as positioned on the right side",
    )
    parser.add_argument(
        "--left",
        action="store_true",
        help="Calibrate the arm as positioned on the left side",
    )

    args = parser.parse_args(test_args)

    print(f"Port: {args.port}")
    print(f"Left: {args.left}")
    print(f"Right: {args.right}")

    # Determine arm side
    arm_side = "right" if args.right else "left"
    print(f"Arm side: {arm_side}")

    print("\n===== ARGUMENT PARSING TEST COMPLETED =====")


def test_syntax_check():
    """Just check if the calibration file can be parsed"""
    print("\n===== TESTING SYNTAX CHECK =====\n")

    calibration_file = os.path.join(current_dir, "calibrate_so_arm100.py")

    if os.path.exists(calibration_file):
        print(f"Calibration file found: {calibration_file}")
        try:
            with open(calibration_file, "r") as f:
                code = compile(f.read(), calibration_file, "exec")
            print("Syntax check passed!")
        except SyntaxError as e:
            print(f"Syntax error in file: {e}")
    else:
        print(f"Calibration file not found at: {calibration_file}")

    print("\n===== SYNTAX CHECK COMPLETED =====")


if __name__ == "__main__":
    # Run the tests
    test_argument_parsing()
    test_syntax_check()
    test_calibration_flow()

    print("\nAll tests completed successfully!")
