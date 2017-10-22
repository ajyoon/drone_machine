from drone_machine import rendering
from drone_machine import osc_interpreter
from drone_machine import sampler_interpreter
from drone_machine import terminal
from drone_machine import writer
from drone_machine.content import the_transistorized_radio as content


out_path = 'out.wav'

sampler_voices = sampler_interpreter.interpret(content.score, content.samplers)
osc_voices = osc_interpreter.interpret(content.score, content.oscillators)
samples = rendering.render(osc_voices, sampler_voices)

writer.write('out.wav', samples)

terminal.bell()
print(f'drone machine finished successfully. data written to {out_path}')
