import wave

import numpy
from tqdm import tqdm

import config
import rendering
import interpreter
import terminal


out_path = 'out.wav'

terminal.clear()
print('drone machine armed...')

voices = interpreter.interpret()
samples = rendering.render(voices)

with wave.open(out_path, 'wb') as out:
    print(f'writing audio data to {out_path}')
    out.setparams(config.wave_params)
    write_chunks = numpy.array_split(samples,
                                     len(samples) // config.framerate)
    for write_chunk in tqdm(write_chunks, f'writing to {out_path}'):
        out.writeframes(write_chunk)

print(f'drone machine finished successfully. data written to {out_path}')
