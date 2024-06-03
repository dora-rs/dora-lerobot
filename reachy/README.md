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
pip install ".[depthai_wrapper]"
cd ..

### Teleoperation Collector
git clone https://github.com/pollen-robotics/reachy2_hdf5_recorder/
```

### To test installaion

```bash
cd reachy2_hdf5_recorder
python3 record_episode_hdf5.py -n test_0 -l 5 --robot_ip 192.168.1.51
```
