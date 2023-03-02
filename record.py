import sounddevice as sd
from scipy.io.wavfile import write
import os

directory = "audio"
prefix = "recording_"
file_format = ".wav"
record_seconds = 20

if not os.path.exists(directory):
    os.makedirs(directory)

try:
    counter = 1
    while True:
        print("Recording...")
        sample_rate = 44100
        duration = record_seconds  # seconds
        frames = duration * sample_rate
        myrecording = sd.rec(int(frames), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()
        filename = os.path.join(directory, prefix + str(counter) + file_format)
        write(filename, sample_rate, myrecording)
        print(f"Saved {filename}")
        counter += 1
except KeyboardInterrupt:
    pass
