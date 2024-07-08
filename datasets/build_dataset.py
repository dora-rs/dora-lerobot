import os
import argparse

import pandas as pd


def main():
    parser = argparse.ArgumentParser(
        description="This script is used to build a dataset from a recording of a set of episodes."
    )

    parser.add_argument("--record-path", type=str, required=True, help="The path to the recording output.")
    parser.add_argument("--dataset-name", type=str, required=True, help="The name you want for the dataset.")
    parser.add_argument("--framerate", type=int, required=False, default=30, help="The framerate of the video.")

    args = parser.parse_args()

    print("Building a new dataset {} from the recording at {}, with framerate {}".format(args.dataset_name,
                                                                                         args.record_path,
                                                                                         args.framerate))

    framerate = args.framerate

    args.dataset_name = args.dataset_name.replace(" ", "_")
    args.dataset_name = args.dataset_name.lower()

    # Load the recording, only keep 'timestamp_utc', and valeus for 'action', 'state', and 'images
    action = pd.read_parquet(args.record_path + "/action.parquet")
    action = action[["timestamp_utc", "action"]]

    episode_index = pd.read_parquet(args.record_path + "/episode_index.parquet")
    episode_index = episode_index[["timestamp_utc", "episode_index"]]

    state = pd.read_parquet(args.record_path + "/observation.state.parquet")
    state = state[["timestamp_utc", "observation.state"]]

    files = os.listdir(args.record_path)
    image_files = [f for f in files if f.startswith("observation.images.") and f.endswith(".parquet")]
    image_files = [f.replace(".parquet", "") for f in image_files]

    images = [pd.read_parquet(args.record_path + "/" + f + ".parquet") for f in image_files]
    images = [images[i][["timestamp_utc", image_files[i]]] for i in range(len(images))]

    # filter rows that are between start and end timestamp, and add the episode_index
    action = pd.DataFrame(action)
    episode_index = pd.DataFrame(episode_index)
    state = pd.DataFrame(state)
    images = [pd.DataFrame(image) for image in images]

    # add "episode_index" column to dataframes
    action["episode_index"] = -1
    state["episode_index"] = -1
    for image in images:
        image["episode_index"] = -1

    # get a list of tuple (episode, start, end) for each episode: an episode start if episode_index != -1 and end if
    # episode_index == -1
    episode_start_end = []

    for i in range(len(episode_index)):
        if episode_index.iloc[i]["episode_index"] != -1:
            episode_start_end.append(
                (episode_index.iloc[i]["episode_index"], episode_index.iloc[i]["timestamp_utc"], None))
        else:
            episode_start_end[-1] = (
                episode_start_end[-1][0], episode_start_end[-1][1], episode_index.iloc[i]["timestamp_utc"])

    # for each dataframe, filter rows that are between start and end timestamp, and add the episode_index
    action = [action[(action["timestamp_utc"] >= episode_start_end[i][1]) & (
            action["timestamp_utc"] <= episode_start_end[i][2])] for i in range(len(episode_start_end))]

    for i in range(len(action)):
        action[i].loc[:, "episode_index"] = episode_start_end[i][0][0]

    action = pd.concat(action, sort=False)

    state = [state[(state["timestamp_utc"] >= episode_start_end[i][1]) & (
            state["timestamp_utc"] <= episode_start_end[i][2])] for i in range(len(episode_start_end))]

    for i in range(len(state)):
        state[i].loc[:, "episode_index"] = episode_start_end[i][0][0]

    state = pd.concat(state, sort=False)

    for i in range(len(images)):
        image = [images[i][(images[i]["timestamp_utc"] >= episode_start_end[j][1]) & (
                images[i]["timestamp_utc"] <= episode_start_end[j][2])] for j in range(len(episode_start_end))]

        for j in range(len(image)):
            image[j].loc[:, "episode_index"] = episode_start_end[j][0][0]

        images[i] = pd.concat(image, sort=False)

    # we merge action, state, and images into a single dataframe, based on the timestamp_utc. Preserve the order of
    # the rows and 'episode_index' column

    dataset = pd.merge(action, state, on=["timestamp_utc", "episode_index"], how="outer")
    for i in range(len(images)):
        dataset = pd.merge(dataset, images[i], on=["timestamp_utc", "episode_index"], how="outer")

    # get the starting timestamp in millis for each episode
    start_timestamp = dataset.groupby("episode_index")["timestamp_utc"].min()
    start_timestamp = start_timestamp.apply(lambda x: pd.to_datetime(x).timestamp() * 1000)

    # transform the timestamp_utc to millis
    dataset["timestamp_utc"] = dataset.apply(
        lambda x: pd.to_datetime(x["timestamp_utc"]).timestamp() * 1000 - start_timestamp[x["episode_index"]], axis=1)

    # load failed_episode_index.parquet
    if os.path.exists(args.record_path + "/failed_episode_index.parquet"):
        failed_episode_index = pd.read_parquet(args.record_path + "/failed_episode_index.parquet")
        failed_episode_index = failed_episode_index[["failed_episode_index"]]

        failed_episode_index = [i[0] for i in failed_episode_index["failed_episode_index"].tolist()]

        # remove the rows for which episode_index is in failed_episode_index
        dataset = dataset[~dataset["episode_index"].isin(failed_episode_index)]

    # for each row with NaN values, fill the NaN values with the nearest non-NaN value
    dataset.set_index(["timestamp_utc", "episode_index"], inplace=True)

    dataset = dataset.ffill().bfill()

    dataset.reset_index(inplace=True)

    # add a new column "frame" to the dataset that is the result of timestamp_utc // framerate
    dataset["frame"] = dataset["timestamp_utc"] // int(1000 / framerate)

    # Only keep 1 row for each frame, keep the first row if there are multiple rows for the same frame
    dataset = dataset.groupby(["episode_index", "frame"]).apply(lambda x: x.iloc[0], include_groups=False).reset_index()

    # Remove timestamp_utc column
    dataset.drop(columns=["timestamp_utc"], inplace=True)

    # Add new column "timestamp" that is the result of frame * framerate
    dataset["timestamp"] = dataset["frame"] * 1000 / framerate

    # Drop the frame column
    dataset.drop(columns=["frame"], inplace=True)

    # only keep the array of positions for each action abd state
    joints = dataset["action"][0][0]["joints"]
    dataset["action"] = dataset["action"].apply(lambda x: x[0]["positions"])
    dataset["observation.state"] = dataset["observation.state"].apply(lambda x: x[0]["positions"])

    # Add a new column "joints" that is the array of joints with enough rows to match the number of rows in the dataset
    dataset["joints"] = pd.Series([joints for _ in range(len(dataset))])

    # save the dataset: mkdir folder, save the dataset as parquet
    if not os.path.exists("datasets/" + args.dataset_name):
        os.makedirs("datasets/" + args.dataset_name)

    dataset.to_parquet("datasets/" + args.dataset_name + "/dataset.parquet", index=False)

    # move the video folder to the dataset folder
    if os.path.exists(args.record_path + "/videos"):
        os.rename(args.record_path + "/videos", "datasets/" + args.dataset_name + "/videos")

    print(dataset)


if __name__ == '__main__':
    main()
