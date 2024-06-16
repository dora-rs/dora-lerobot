## Reachy 1

### Teleoperation

```bash
git clone https://github.com/pollen-robotics/reachy2_hdf5_recorder/
cd reachy2_hdf5_recorder
pip install -r requirements.txt
```
#### Installation dora-lerobot

```bash
## Create new python environment

cargo install dora-rs --locked
pip install dora-rs
```
### AI Pipeline

### Robot manipulation

Click on the button on the base to turn on the robot, then click on the button on the shoulder of the robot.\
Make sure the emergency button is not pressed in.

### Data Collection

```bash
cd reachy2_hdf5_recorder
python reachy1_record_episodes_hdf5.py -n <recording_session_name>_raw -l <epiodes_duration in s>
```

```bash
git clone https://github.com/huggingface/lerobot.git && cd lerobot
git checkout origin/user/rcadene/2024_06_03_reachy2
pip install -e .

# Must have a HugginFace token with write permission in https://huggingface.co/settings/tokens
huggingface-cli login --token ${HUGGINGFACE_TOKEN} --add-to-git-credential

cd ../reachy2_hdf5_recorder
python ../lerobot/lerobot/scripts/push_dataset_to_hub.py 
    -data-dir data 
    --dataset-id <recording_session_name>
    --raw-format reachy2_hdf5 
    --community-id <HuggingFace_id>

```

### Training

```bash
python lerobot/scripts/train.py 
    policy=act_reachy2_real 
    env=dora_reachy2_real 
    wandb.enable=true 
    hydra.run.dir=<recording_session_name> 
    env.state_dim=8 
    nv.action_dim=8 
    dataset_repo_id=<HuggingFace_id>/<recording_session_name>
```

### Evaluation

Inside of the file `lerobot/<recording_session_name>/checkpoints/last/pretrained_model/config.yaml` change the env.task from DoraReachy2-v0 to DoraReachy1-v0.

Make sure to get the right path for the source and args of eval in the file eval.yml

```bash

dora start reachy/graphs/eval.yml --attach
```

### Reachy Initialization

```bash
ssh bedrock@192.168.1.51
```

```bashH
cd dev_docker
sudo service stop


docker compose -f mode/dev.yaml up -d core

docker exec -it core bash

# In the docker container

ros2 launch reachy_bringup reachy.launch.py start_sdk_server:=true
```
