import config


class Keyframe:
    """A voice's amplitude keyframe.

    `Keyframe`s must be considered immutable.
    After initialization, they must not be modified.
    """

    def __init__(self, time, amplitude):
        """
        Args:
            time (float): Time in seconds of this frame
            amplitude (float): 0-1 amplitude at this frame.
        """
        self.time = time
        self.amplitude = amplitude
        self.sample_pos = int(config.framerate * self.time)
