"Visualize delays between frames and frame drops."
import pickle
import matplotlib.pyplot as plt


class Timestamps:
    def __init__(self, path):
        self.path = path
        self.dict = {}
        self.frames = []
        self.deltas = []

        self.load()
        self.extract()

    def plot(self):
        _, ax = plt.subplots()
        ax.plot(self.frames, self.deltas)
        ax.set_xlabel("Frames")
        ax.set_ylabel("Deltas")
        return ax

    def extract(self):
        self.frames = sorted(self.dict.keys())

        x = self.dict[self.frames[0]]
        for f in self.frames:
            self.deltas.append(self.dict[f] - x)
            x = self.dict[f]

    def load(self):
        with open(self.path, 'rb') as handle:
            self.dict = pickle.load(handle)


if __name__ == "__main__":
    import argparse
    import glob

    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("-p", "--path",
                        help="Path to the directory containg the timestamps",
                        dest="path")


    args = parser.parse_args()
    path = args.path
    paths = sorted(glob.glob(path + '*.pickle'))

    frames = []
    deltas = []
    _, ax = plt.subplots()
    for i, p in enumerate(paths):
        t = Timestamps(p)
        frames.append(t.frames)
        deltas.append(t.deltas)
        ax.plot(t.frames, t.deltas, label=p)
        m = max(t.frames)

    ax.set_xlabel("Frame #")
    ax.set_ylabel("Deltas (s)")
    ax.legend()
    plt.show()
