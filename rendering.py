import ctypes
import multiprocessing
import time
import random

import numpy

from tqdm import tqdm

import config
import terminal


def samples_needed(voices):
    max_sample = 0
    for voice in voices:
        for keyframe in voice.keyframes:
            if max_sample < keyframe.sample_pos:
                max_sample = keyframe.sample_pos
    return max_sample


def normalize(array, value):
    max_value = max(array.max(), abs(array.min()))
    for i in range(len(array)):
        array[i] = (array[i] / max_value) * value


def split_voices(voices, n_groups):
    """Randomly breaak `voices` into a number of groups"""
    voices = voices[:]
    random.shuffle(voices)
    return numpy.array_split(voices, n_groups)


class Work:
    def __init__(self, process, progress, progress_bar):
        self.process = process
        self.progress = progress
        self.progress_bar = progress_bar


def render(voices):
    num_samples = samples_needed(voices)
    data_array = multiprocessing.Array(ctypes.c_double, num_samples)
    voice_groups = split_voices(voices, config.processes)

    remaining_work = []
    for group in voice_groups:
        progress = multiprocessing.Value(ctypes.c_ulonglong, 0)
        process = multiprocessing.Process(
            target=render_worker,
            args=(group, data_array, 0, num_samples, progress))
        process.start()
        progress_bar = tqdm(total=num_samples,
                            desc=f'rendering pid {process.pid}')
        remaining_work.append(Work(process, progress, progress_bar))

    while True:
        for work in remaining_work:
            work.progress_bar.update(work.progress.value - work.progress_bar.n)
            if not work.process.is_alive():
                work.progress_bar.close()
        remaining_work = [w for w in remaining_work if w.process.is_alive()]
        if not remaining_work:
            break
        time.sleep(0.5)

    terminal.clear()
    print('sample rendering complete...')
    samples = numpy.frombuffer(data_array.get_obj())
    print('normalizing data...')
    normalize(samples, 32767)
    print(f'converting to output dtype {config.dtype.__name__}')
    return samples.astype(config.dtype)


def render_worker(voices, data_array, start, end, progress):
    """Worker process method. Mutates data_array in place with locking."""
    chunks = []
    max_chunks = ((config.worker_data_size * random.uniform(0.8, 1.2))
                  / config.chunk_size)
    last_write_pos = 0
    for pos in range(start, end + config.chunk_size, config.chunk_size):
        chunk = numpy.zeros(config.chunk_size)
        for voice in voices:
            voice_samples = voice.get_samples_at(pos, config.chunk_size)
            if voice_samples is not None:
                chunk = chunk + voice_samples
        chunks.append(chunk)
        # No lock needed since we're the only process writing to this
        progress.value = pos

        if len(chunks) > max_chunks:
            write_samples(chunks, data_array, last_write_pos)
            chunks = []
            last_write_pos = pos

    write_samples(chunks, data_array, last_write_pos)


def write_samples(chunks, data_array, offset):
    samples = numpy.concatenate(chunks)
    samples.resize((len(data_array),))
    with data_array.get_lock():
        np_array = numpy.frombuffer(data_array.get_obj())[offset:]
        if len(samples) > len(np_array):
            samples.resize(len(np_array))
        np_array += samples
