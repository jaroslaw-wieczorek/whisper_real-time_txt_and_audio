import os
from pydub import AudioSegment
import argparse

parser = argparse.ArgumentParser(description='Concatenate WAV files')
parser.add_argument("-i", "--input_directory", type=str, default="./records", help="Input directory for WAV files")
parser.add_argument("-p", "--prefix", type=str, default="recording_", help="Prefix for input WAV files")
parser.add_argument("-o", "--output_file", type=str, default="output.wav", help="Output file name")

args = parser.parse_args()

directory = args.input_directory
output_file = args.output_file
prefix = args.prefix

files = [os.path.join(directory, file) for file in os.listdir(directory) if file.startswith(prefix) and file.endswith(".wav")]
files = sorted(files, key=lambda x: int(x.split("_")[-1].split(".")[0]))

output = AudioSegment.empty()
if files:
    print("# Start processing files")
    print(f"Files list: {files}")
    for file in files:
        print(f" - open {file}")
        sound = AudioSegment.from_file(file, format="wav")
        output += sound
    output.export(os.path.join(os.path.abspath(directory), output_file), format="wav")
else:
   print(f"Directory: {directory} doesn't contains WAV files with prefix: {prefix}")
