import numpy

from spectrophone import config


class Voice:

    __slots__ = (
        'oscillator',
        'keyframes',
        'last_frame_i'
    )

    def __init__(self, oscillator):
        self.oscillator = oscillator
        self.last_frame_i = 0
        # A list of (sample_pos, amplitude) keyframe tuples
        self.keyframes = []

    @property
    def max_sample_pos(self):
        return max((f[0] for f in self.keyframes), default=0)

    def finalize(self, keyframes_need_sort=True):
        """Finalize the voice's keyframes.

        Must be called before `get_samples_at` may be safely called.
        """
        if keyframes_need_sort:
            self.keyframes.sort(key=lambda k: k[0])
        # Prevent popping on voice entry
        self.keyframes[0] = (self.keyframes[0][0], 0)
        self.keyframes[-1] = (self.keyframes[-1][0], 0)
        self.keyframes = numpy.array(self.keyframes, dtype='uint32, f16')

    def get_samples_at(self, sample_pos, chunk_size):
        """Get a chunk of `chunk_size` from the voice at `sample_pos`.

        This is an extremely hot code path; optimize carefully.
        """
        if self.last_frame_i == len(self.keyframes) - 1:
            return self.oscillator.get_samples(chunk_size,
                                               self.keyframes[-1][1])

        last_frame = self.keyframes[self.last_frame_i]
        next_frame = self.keyframes[self.last_frame_i + 1]

        if (last_frame[1] == next_frame[1]):
            amplitude = last_frame[1]
        else:
            # Linear interpolate amplitude
            amplitude = (
                last_frame[1] + (
                    (sample_pos - last_frame[0]) * (
                        (next_frame[1] - last_frame[1]) /
                        (next_frame[0] - last_frame[0])
                    )
                )
            )
        # Prepare for next iteration
        if sample_pos >= self.keyframes[self.last_frame_i + 1][0]:
            self.last_frame_i += 1

        # Shortcut on silence
        if (amplitude < config.silence_threshold and
                self.oscillator.last_amplitude < config.silence_threshold):
            return None

        # Render
        return self.oscillator.get_samples(chunk_size, amplitude)
