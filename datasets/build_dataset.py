import os
import argparse
import warnings
from dataclasses import dataclass, field
from typing import ClassVar, Any

import pandas as pd
import pyarrow as pa

from datasets import Dataset, Features, Image, Sequence, Value
from datasets.features.features import register_feature


def get_episode_info(path):
    episode_index = pd.read_parquet(path + "/episode_index.parquet")
    episode_index = episode_index[["timestamp_utc", "episode_index"]]
    episode_index = pd.DataFrame(episode_index)

    episode_info = []

    for i in range(len(episode_index)):
        if episode_index.iloc[i]["episode_index"][0] != -1:
            episode_info.append(
                (
                    episode_index.iloc[i]["episode_index"][0],
                    episode_index.iloc[i]["timestamp_utc"],
                    None,
                )
            )
        else:
            episode_info[-1] = (
                episode_info[-1][0],
                episode_info[-1][1],
                episode_index.iloc[i]["timestamp_utc"],
            )

    if os.path.exists(path + "/failed_episode_index.parquet"):
        failed_episode_index = pd.read_parquet(path + "/failed_episode_index.parquet")
        failed_episode_index = failed_episode_index[["failed_episode_index"]]

        failed_episode_index = [
            i[0] for i in failed_episode_index["failed_episode_index"].tolist()
        ]

        episode_info = [
            episode
            for episode in episode_info
            if episode[0] not in failed_episode_index
        ]

    return episode_info


def get_observation_images(path):
    files = os.listdir(path)
    image_files = [
        f
        for f in files
        if f.startswith("observation.images.") and f.endswith(".parquet")
    ]

    return [f.replace(".parquet", "") for f in image_files]


def adapt_timestamps(dataframe):
    dataframe["timestamp"] = dataframe["timestamp_utc"]

    start_timestamp = dataframe.groupby("episode_index")["timestamp"].min()
    start_timestamp = start_timestamp.apply(
        lambda x: pd.to_datetime(x).timestamp() * 1000
    )

    dataframe["timestamp"] = dataframe.apply(
        lambda x: pd.to_datetime(x["timestamp"]).timestamp() * 1000
        - start_timestamp[x["episode_index"]],
        axis=1,
    )

    return dataframe


def load_dataframe(path, name, episode_info):
    df = pd.read_parquet(path, f"/{name}.parquet")
    df = df[["timestamp_utc", "action"]]
    df = pd.DataFrame(df)

    df["episode_index"] = -1
    df = [
        df[
            (df["timestamp_utc"] >= episode_info[i][1])
            & (df["timestamp_utc"] <= episode_info[i][2])
        ]
        for i in range(len(episode_info))
    ]

    for i in range(len(df)):
        df[i].loc[:, "episode_index"] = episode_info[i][0]

    df = pd.concat(df, sort=False)
    df = adapt_timestamps(df)

    return df


def create_dataset(action, state, images):
    dataset = pd.merge(action, state, on=["timestamp", "episode_index"], how="outer")
    for i in range(len(images)):
        dataset = pd.merge(
            dataset, images[i], on=["timestamp", "episode_index"], how="outer"
        )

    dataset.sort_values(by=["episode_index", "timestamp"], inplace=True)

    return dataset


def save_dataset_state(dataset, dataset_name, name):
    if not os.path.exists("datasets/" + dataset_name):
        os.makedirs("datasets/" + dataset_name)

    dataset.to_parquet("datasets/" + dataset_name + f"/{name}.parquet", index=False)


def fill_dataset(dataset):
    dataset.set_index(["timestamp", "episode_index"], inplace=True)
    dataset = dataset.ffill().bfill()
    dataset.reset_index(inplace=True)


@dataclass
class VideoFrame:
    pa_type: ClassVar[Any] = pa.struct({"path": pa.string(), "timestamp": pa.float32()})
    _type: str = field(default="VideoFrame", init=False, repr=False)

    def __call__(self):
        return self.pa_type


with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        "'register_feature' is experimental and might be subject to breaking changes in the future.",
        category=UserWarning,
    )
    # to make VideoFrame available in HuggingFace `datasets`
    register_feature(VideoFrame, "VideoFrame")


def to_hf_dataset(dataset) -> Dataset:
    features = {}

    keys = [key for key in dataset if "observation.images." in key]
    for key in keys:
        features[key] = VideoFrame()

    features["observation.state"] = Sequence(
        length=dataset["observation.state"].shape[1],
        feature=Value(dtype="float32", id=None),
    )
    features["action"] = Sequence(
        length=dataset["action"].shape[1], feature=Value(dtype="float32", id=None)
    )
    features["episode_index"] = Value(dtype="int64", id=None)
    features["frame_index"] = Value(dtype="int64", id=None)
    features["timestamp"] = Value(dtype="float32", id=None)
    features["next.done"] = Value(dtype="bool", id=None)
    features["index"] = Value(dtype="int64", id=None)

    hf_dataset = Dataset.from_dict(dataset, features=Features(features))
    return hf_dataset


def main():
    parser = argparse.ArgumentParser(
        description="This script is used to build a dataset from a recording of a set of episodes."
    )

    parser.add_argument(
        "--record-path",
        type=str,
        required=True,
        help="The path to the recording output.",
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        required=True,
        help="The name you want for the dataset.",
    )
    parser.add_argument(
        "--framerate",
        type=int,
        required=False,
        default=30,
        help="The framerate of the video.",
    )

    args = parser.parse_args()

    print(
        "Building a new dataset {} from the recording at {}, with framerate {}".format(
            args.dataset_name, args.record_path, args.framerate
        )
    )

    framerate = args.framerate

    args.dataset_name = args.dataset_name.replace(" ", "_")
    args.dataset_name = args.dataset_name.lower()

    episode_info = get_episode_info(args.record_path)
    images = get_observation_images(args.record_path)

    action = load_dataframe(args.record_path, "action", episode_info)
    state = load_dataframe(args.record_path, "observation.state", episode_info)
    images = [load_dataframe(args.record_path, image, episode_info) for image in images]

    dataset = create_dataset(action, state, images)

    save_dataset_state(dataset, args.dataset_name, "raw")

    fill_dataset(dataset)

    dataset["frame_index"] = dataset["timestamp"] // int(1000 / framerate)

    dataset["index"] = dataset["timestamp_utc"] // int(1000 / framerate)
    dataset.drop(columns=["timestamp_utc"], inplace=True)

    dataset = (
        dataset.groupby(["episode_index", "frame_index"])
        .apply(lambda x: x.iloc[0], include_groups=False)
        .reset_index()
    )

    dataset.sort_values(by=["episode_index", "timestamp"], inplace=True)

    dataset["next.done"] = False

    for episode_index in dataset["episode_index"].unique():
        last_frame = dataset[dataset["episode_index"] == episode_index].iloc[-1]
        dataset.loc[
            (dataset["episode_index"] == episode_index)
            & (dataset["frame_index"] == last_frame["frame_index"]),
            "next.done",
        ] = True

    joints = pa.StructArray.from_pandas(dataset["action"][0])
    joints = joints.field("joints").to_numpy(zero_copy_only=False)
    dataset["joints"] = pd.Series([joints for _ in range(len(dataset))])

    def get_values(x):
        x = pa.StructArray.from_pandas(x)
        return x.field("values").to_numpy(zero_copy_only=False)

    dataset["action"] = dataset["action"].apply(lambda x: get_values(x))
    dataset["observation.state"] = dataset["observation.state"].apply(
        lambda x: get_values(x)
    )

    dataset.sort_values(by=["episode_index", "timestamp"], inplace=True)
    save_dataset_state(dataset, args.dataset_name, "dataset")

    if os.path.exists(args.record_path + "/videos"):
        os.rename(
            args.record_path + "/videos", "datasets/" + args.dataset_name + "/videos"
        )

    hf_dataset = to_hf_dataset(dataset)

    hf_dataset.save_to_disk(f"datasets/{args.dataset_name}/hf_dataset")


if __name__ == "__main__":
    main()
