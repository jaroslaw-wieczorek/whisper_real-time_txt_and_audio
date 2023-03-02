import os
from pydub import AudioSegment

directory = "./"
prefix = "recordings_"
output_file = "output.wav"

files = [os.path.join(directory, file) for file in os.listdir(directory) if file.startswith(prefix)]
files = sorted(files, key=lambda x: int(x.split("_")[-1].split(".")[0]))
print(files)

output = AudioSegment.empty()

for file in files:
    sound = AudioSegment.from_file(file, format="wav")
    output += sound

output.export(os.path.join(directory, output_file), format="wav")
