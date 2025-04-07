# SO-ARM100 Calibration Guide

Proper calibration is essential for the SO-ARM100 robotic arm to function correctly with the Dora framework. This guide will help you understand the calibration process and how to use the `calibrate_so_arm100.py` script.

## Why Calibration is Important

Calibration ensures that:
1. The arm's physical positions are correctly mapped to logical angles
2. Your arm's movements are predictable and precise
3. The software can accurately control each joint
4. Teleoperation works as expected
5. Recorded movements can be replicated reliably

If your arm is not calibrated correctly, it may:
- Move unpredictably
- Fail to reach target positions
- Behave differently from other SO-ARM100 arms

## Using the Calibration Script

We've provided a simplified calibration script (`calibrate_so_arm100.py`) that guides you through the process.

### Prerequisites

Before running the calibration script:
1. Make sure your SO-ARM100 is fully assembled
2. Connect the arm to your computer
3. Install all required packages (run `pip install -r requirements.txt`)
4. Ensure your user has permission to access the serial port

### Running the Script

```bash
cd dora-lerobot/

# Activate your environment
source venv/bin/activate  # On Linux
# or
source venv/Scripts/activate  # On Windows bash
# or
venv\Scripts\activate.bat  # On Windows cmd
# or
venv\Scripts\activate.ps1  # On Windows PowerShell

# Run the calibration script
python ./robots/so100/calibrate_so_arm100.py --port <YOUR_PORT> --left
# Or use --right if your arm is positioned on the right side
```

Replace `<YOUR_PORT>` with your serial port (e.g., `/dev/ttyUSB0` on Linux or `COM3` on Windows).

### Calibration Positions

The calibration requires setting the arm to two reference positions:

#### Position 1
- Arm extended straight forward
- Elbow at 90 degrees
- Wrist straight
- Gripper open

This position corresponds to logical angles of:
- shoulder_pan: 0°
- shoulder_lift: -90°
- elbow_flex: 90°
- wrist_flex: 0°
- wrist_roll: -90°
- gripper: 0° (open)

#### Position 2
- Shoulder rotated 90 degrees
- Arm straight horizontally
- Wrist bent 90 degrees
- Gripper closed

This position corresponds to logical angles of:
- shoulder_pan: 90°
- shoulder_lift: 0°
- elbow_flex: 0°
- wrist_flex: 90°
- wrist_roll: 0°
- gripper: -90° (closed)

### The Calibration Process

1. The script first disables torque on all motors so you can move them manually
2. You'll position the arm in Position 1 and confirm
3. You'll position the arm in Position 2 and confirm
4. The script calculates the PWM-to-logical and logical-to-PWM conversion tables
5. The configuration is saved to a JSON file
6. The script enters a verification mode where you can move the arm and see the calculated logical angles

### Understanding the Configuration File

The calibration creates a JSON file (e.g., `follower.left.json`) that contains:
- Motor IDs for each joint
- Motor model information
- PWM-to-logical conversion parameters
- Logical-to-PWM conversion parameters

This file is used by the Dora nodes to translate between logical angles (in degrees) and motor PWM values.

### Troubleshooting

If you encounter issues during calibration:

1. **Connection Errors:**
   - Ensure you're using the correct port
   - Check that you have permission to access the port
   - Verify the arm is powered and connected

2. **Movement Problems:**
   - Ensure all servos are responding (check LED indicators)
   - Verify the arm isn't physically obstructed

3. **Alignment Issues:**
   - Take your time positioning the arm accurately
   - Use a square or angle guides to ensure proper joint angles

4. **Configuration File Errors:**
   - Ensure the `configs` directory exists and is writable
   - Check for error messages during the saving process

## Using Your Calibration

After calibration, you'll use the generated configuration file in your Dora graph:

```yaml
nodes:
  - id: so100-follower
    env:
      PORT: /dev/ttyUSB0  # Your port
      CONFIG: ../configs/follower.left.json  # Your config file
      
  - id: lcr-to-so100
    env:
      FOLLOWER_CONTROL: ../configs/follower.left.json  # Your config file
```

## License

This library is licensed under the [Apache License 2.0](../../LICENSE). 