#!/usr/bin/env python
"""
SO-ARM100 Calibration Script

This script guides users through a simplified calibration process for the SO-ARM100 robot arm.
It helps users:
1. Connect to the arm
2. Disable torque to allow manual positioning
3. Set the arm to reference positions
4. Calibrate the arm's joints
5. Verify calibration by moving to test positions
6. Save calibration data for future use

Usage:
    python calibrate_so_arm100.py --port <PORT> [--left/--right]
"""

import argparse
import json
import time
import os
import sys

# Define dependencies explicitly
missing_deps = []

try:
    import pyarrow as pa
except ImportError:
    missing_deps.append("pyarrow")

try:
    from bus import FeetechBus, TorqueMode, OperatingMode
except ImportError:
    missing_deps.append("bus module (part of SO-ARM100 support)")

try:
    from pwm_position_control.transform import pwm_to_logical_arrow
    from pwm_position_control.tables import (
        construct_logical_to_pwm_conversion_table_arrow,
        construct_pwm_to_logical_conversion_table_arrow,
    )
    from pwm_position_control.functions import construct_control_table
except ImportError:
    missing_deps.append(
        "pwm-position-control (install via: pip install git+https://github.com/Hennzau/pwm-position-control)"
    )

# Check if required dependencies are missing
if missing_deps:
    print(
        "Error: Required modules not found. Make sure you're in the correct environment."
    )
    print("Missing dependencies:")
    for dep in missing_deps:
        print(f" - {dep}")
    print("\nInstallation instructions:")
    print("1. Ensure you're in the correct virtual environment")
    print("2. Install required packages:")
    print("   pip install pyarrow")
    print("   pip install -r robots/so100/requirements.txt")
    print("   pip install git+https://github.com/Hennzau/pwm-position-control")
    sys.exit(1)

# Define joint names for easier referencing
FULL_ARM = pa.array(
    [
        "shoulder_pan",
        "shoulder_lift",
        "elbow_flex",
        "wrist_flex",
        "wrist_roll",
        "gripper",
    ],
    type=pa.string(),
)


# Helper function to wait for user input
def pause(message="Press Enter to continue..."):
    input(message)


# Helper function to wrap joints and values
def wrap_joints_and_values(joints, values):
    return pa.StructArray.from_arrays(
        arrays=[joints, values],
        names=["joints", "values"],
    )


def calibrate_arm(port, arm_side):
    """
    Main calibration function for SO-ARM100

    Args:
        port: Serial port for the arm connection
        arm_side: 'left' or 'right' indicating the arm's position
    """
    print("\n===== SO-ARM100 Calibration Tool =====")
    print(f"Port: {port}")
    print(f"Arm Side: {arm_side}")
    print("=====================================\n")

    # Define reference positions for calibration
    # Position 1: Arm straight out, gripper open
    # Position 2: Arm at 90 degrees, gripper closed
    reference_positions = (
        wrap_joints_and_values(FULL_ARM, [0, -90, 90, 0, -90, 0]),
        wrap_joints_and_values(FULL_ARM, [90, 0, 0, 90, 0, -90]),
    )

    # Initialize connection to the arm
    try:
        print(f"Connecting to SO-ARM100 on port {port}...")
        arm = FeetechBus(
            port,
            {
                "shoulder_pan": (1, "st3215"),
                "shoulder_lift": (2, "st3215"),
                "elbow_flex": (3, "st3215"),
                "wrist_flex": (4, "st3215"),
                "wrist_roll": (5, "st3215"),
                "gripper": (6, "st3215"),
            },
        )
        print("Connection successful!")
    except Exception as e:
        print(f"Error connecting to the arm: {e}")
        print("Please check the port and try again.")
        return False

    # Configure servos for calibration (disable torque)
    print("\nDisabling torque to allow manual positioning...")
    try:
        arm.write_torque_enable(
            wrap_joints_and_values(FULL_ARM, [TorqueMode.DISABLED.value] * 6)
        )

        arm.write_operating_mode(
            wrap_joints_and_values(FULL_ARM, [OperatingMode.ONE_TURN.value] * 6)
        )

        # Reset angle limits
        arm.write_max_angle_limit(
            wrap_joints_and_values(FULL_ARM, [pa.scalar(0, pa.uint32())] * 6)
        )

        arm.write_min_angle_limit(
            wrap_joints_and_values(FULL_ARM, [pa.scalar(0, pa.uint32())] * 6)
        )
        print("Servos configured successfully!")
    except Exception as e:
        print(f"Error configuring servos: {e}")
        return False

    # Position 1 Calibration
    print("\n=== Position 1 Calibration ===")
    print("Please move the arm to Position 1:")
    print("- Arm extended straight forward")
    print("- Elbow at 90 degrees")
    print("- Wrist straight")
    print("- Gripper open")
    print("\nRefer to the diagram in CONFIGURING.md for visual guidance")

    pause()

    try:
        pwm_position_1 = arm.read_position(FULL_ARM)["values"].values
        print("Position 1 recorded!")
    except Exception as e:
        print(f"Error reading position: {e}")
        return False

    # Position 2 Calibration
    print("\n=== Position 2 Calibration ===")
    print("Please move the arm to Position 2:")
    print("- Shoulder rotated 90 degrees")
    print("- Arm straight horizontally")
    print("- Wrist bent 90 degrees")
    print("- Gripper closed")
    print("\nRefer to the diagram in CONFIGURING.md for visual guidance")

    pause()

    try:
        pwm_position_2 = arm.read_position(FULL_ARM)["values"].values
        print("Position 2 recorded!")
    except Exception as e:
        print(f"Error reading position: {e}")
        return False

    print("\nCalibration positions recorded successfully!")

    # Create conversion tables
    print("\nCalculating calibration parameters...")
    pwm_positions = (pwm_position_1, pwm_position_2)

    try:
        pwm_to_logical_conversion_table = (
            construct_pwm_to_logical_conversion_table_arrow(
                pwm_positions, reference_positions
            )
        )
        logical_to_pwm_conversion_table = (
            construct_logical_to_pwm_conversion_table_arrow(
                pwm_positions, reference_positions
            )
        )

        # Create the control table
        control_table_json = {}
        for i in range(len(FULL_ARM)):
            control_table_json[FULL_ARM[i].as_py()] = {
                "id": i + 1,
                "model": "sts3215",
                "torque": True,
                "pwm_to_logical": pwm_to_logical_conversion_table[FULL_ARM[i].as_py()],
                "logical_to_pwm": logical_to_pwm_conversion_table[FULL_ARM[i].as_py()],
            }

        # Ensure the config directory exists
        config_dir = "./robots/so100/configs"
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        # Save the configuration
        config_path = f"{config_dir}/follower.{arm_side}.json"
        with open(config_path, "w") as file:
            json.dump(control_table_json, file)

        print(f"Calibration saved to: {config_path}")
    except Exception as e:
        print(f"Error computing calibration: {e}")
        return False

    # Verification phase - real-time feedback
    print("\n=== Calibration Verification ===")
    print("You can now move the arm to verify calibration.")
    print("The script will show real-time joint angles.")
    print("Press Ctrl+C to exit when finished.")

    try:
        control_table = construct_control_table(
            pwm_to_logical_conversion_table, logical_to_pwm_conversion_table
        )

        print("\nStarting real-time position feedback...")
        print("(Press Ctrl+C to exit)")

        while True:
            pwm_position = arm.read_position(FULL_ARM)
            logical_position = pwm_to_logical_arrow(
                pwm_position, control_table, ranged=True
            ).field("values")

            # Print current position in a cleaner format
            positions = {}
            for i, joint in enumerate(FULL_ARM):
                positions[joint.as_py()] = round(logical_position[i].as_py(), 1)

            # Clear line and print current position
            print(f"\rPositions: {positions}", end="")
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\n\nCalibration verification complete!")
    except Exception as e:
        print(f"\nError during verification: {e}")

    print("\n=== Calibration Complete ===")
    print(f"Configuration saved to: {config_path}")
    print("You can now use this configuration in your Dora graphs")
    print("Example usage in a graph file:")
    print(
        f"""
    nodes:
      - id: so100-follower
        env:
          PORT: {port}
          CONFIG: ../configs/follower.{arm_side}.json
          
      - id: lcr-to-so100
        env:
          FOLLOWER_CONTROL: ../configs/follower.{arm_side}.json
    """
    )

    return True


def main():
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

    args = parser.parse_args()

    # Validate arguments
    if args.right and args.left:
        print("Error: You cannot specify both --right and --left.")
        return

    if not (args.right or args.left):
        print("Error: You must specify either --right or --left.")
        return

    arm_side = "right" if args.right else "left"

    # Run calibration
    calibrate_arm(args.port, arm_side)


if __name__ == "__main__":
    main()
