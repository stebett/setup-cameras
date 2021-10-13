import glob
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

    video_path = "/home/bettani/setup-cameras/videos/camera1/"
    paths = sorted(glob.glob(video_path + '*.pickle'))

    expectation = 10

    frames = []
    deltas = []
    _, ax = plt.subplots()
    for i, p in enumerate(paths):
        t = Timestamps(p)
        frames.append(t.frames)
        deltas.append(t.deltas)
        ax.plot(t.frames, t.deltas, label=p[-13:-7])
        m = max(t.frames)
        e = expectation * (i + 1) - 1
        if m > e:
            ax.hlines(-0.01, e, m, colors='r', linestyles='dotted')
        elif m < e:
            ax.hlines(-0.01, m, e, colors='g', linestyles='dotted')

    ax.set_xlabel("Frame #")
    ax.set_ylabel("Deltas (s)")
    ax.legend()
    plt.show()
