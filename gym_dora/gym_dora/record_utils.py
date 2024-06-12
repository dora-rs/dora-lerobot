from pathlib import Path
import os
import subprocess

from glob import glob

camera_names = ["cam_trunk"]
session_path = os.path.join(
    "data",
)
FPS = 30


def encode_video_frames(imgs_dir: Path, video_path: Path, fps: int, cam_name: str):
    """More info on ffmpeg arguments tuning on `lerobot/common/datasets/_video_benchmark/README.md`"""
    video_path = Path(video_path)
    video_path.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg_cmd = (
        f"ffmpeg -r {fps} "
        "-f image2 "
        "-loglevel error "
        f"-i {str(imgs_dir)}/{cam_name}_%d.png "
        "-vcodec libx264 "
        "-g 2 "
        "-pix_fmt yuv444p "
        f"{str(video_path)}"
    )

    subprocess.run(ffmpeg_cmd.split(" "), check=True)


print("Encoding video ...")
for cam_name in camera_names:
    encode_video_frames(
        Path(f"{session_path}/images_episode_{episode_id}"),
        Path(f"{session_path}/episode_{episode_id}_{cam_name}.mp4"),
        30,
        cam_name,
    )
print("Done encoding video!")

print("Removing raw images ...")
for cam_name in camera_names:
    for f in glob(f"{session_path}/images_episode_{episode_id}/{cam_name}_*.png"):
        os.remove(f)

print("Saved!")
