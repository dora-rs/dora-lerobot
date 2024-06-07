## Reachy 2

### Installation

```bash
### Install the sdk
git clone https://github.com/pollen-robotics/reachy2-sdk
cd reachy2-sdk
pip install -e .
cd ..

### Connect Camera USB
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="03e7", MODE="0666"' | sudo tee /etc/udev/rules.d/80-movidius.rules
sudo udevadm control --reload-rules && sudo udevadm trigger

### Install Polen vision
git clone https://github.com/pollen-robotics/pollen-vision.git
cd pollen-vision
git checkout lerobot_only_left_camera
pip install ".[depthai_wrapper]"
cd ..

### Teleoperation Collector
git clone https://github.com/pollen-robotics/reachy2_hdf5_recorder/
```

### To record data
```bash
cd reachy2_hdf5_recorder
python3 record_episodes_hdf5.py -n <recording_session_name>_raw -l <epiodes_duration in s> -r <framerate> --robot_ip <robot_ip>
```

```bash
huggingface-cli upload \
                <hf-organisation>/<dataset_name> \
                data/<recording_session_name>_raw/ \
                --repo-type dataset (--private)
```


### 06/07/2021
As of today, we need to use several branches:
- mobile_base : branch 21 # server side, install manually
- reachy-sdk-api : branch 116 # server and client side, install manually
- mobile-base-sdk : branch 25  # client side, install manually
- reachy2-sdk-server : branch 135 # server side, install mannually