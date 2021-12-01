"Visualize delays between frames and frame drops."
import pickle
import matplotlib.pyplot as plt
from pathlib import Path


class Timestamps:
    def __init__(self, path):
        self.name = path.stem
        self.path = path
        self.cam = path.parent.name
        self.dict = {}
        self.frames = []
        self.deltas = []
        self.times = []
        self.loss = 0

        self.load()
        self.extract()

    def plot(self):
        _, ax = plt.subplots()
        ax.plot(self.frames, self.deltas)
        ax.set_xlabel("Frames")
        ax.set_ylabel("Deltas")
        ax.legend(self.path.stem)
        return ax

    def extract(self):
        self.loss = self.dict.pop("loss")
        self.frames = sorted(self.dict.keys())
        self.times = sorted(self.dict.values())
        self.deltas = [self.times[i] - self.times[i-1] for i in range(1, len(self.times))]
        self.deltas.insert(0, self.deltas[0])


    def load(self):
        with open(self.path, 'rb') as handle:
            self.dict = pickle.load(handle)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("-p", "--path",
                        help="Path to the directory containg the cameras",
                        dest="path", default="~/data", 
                        type=lambda x: Path(x).expanduser().absolute())
    parser.add_argument("--cam-prefix",
                        help="Prefix of directories for each cam (ex. [cam]1, [cam]2)",
                        dest="prefix", default="cam")


    args = parser.parse_args()
    path = args.path
    prefix = args.prefix
    cameras = sorted(path.glob(f"{prefix}*"))
    timestamps = []
    for cam in cameras:
        pickles = sorted(cam.glob("*.pickle"))
        ts = [Timestamps(p) for p in pickles]
        if len(ts) == 0:
            continue
        timestamps.append(ts)

    fig, _ = plt.subplots(len(cameras))

    i = 0
    for cam_ts in timestamps:
        total_loss = 0
        ax = fig.axes[i]
        for ts in cam_ts:
            ax.plot(ts.frames, ts.deltas, label=f"{ts.name} loss: {ts.loss}")
            total_loss += ts.loss

        ax.set_title(f"Camera {ts.cam} loss: {total_loss}")
        ax.set_xlabel("Frame #")
        ax.set_ylabel("Deltas (s)")
        ax.legend()
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        i += 1

    plt.subplots_adjust(hspace = 0.7, right=0.8)
    plt.show()
