import sounddevice as sd
import numpy as np
import whisper
import asyncio
import queue
import signal
import sys
import time
from scipy.io import wavfile
import logging

# SETTINGS

# Auto download the model used for transcription. https://github.com/openai/whisper#available-models-and-languages
MODEL_TYPE="base.en"

# Set english language to avoid autodetection
LANGUAGE="English"

# This is the base chunk size the audio is split into in samples. 
# Count blocksize / samplerate = chunk length in seconds. 
BLOCKSIZE=160000 

# Should be set to the lowest sample amplitude that the speech in the audio material has
SILENCE_THRESHOLD=400

# Number of samples in one buffer that are allowed to be higher than threshold
SILENCE_RATIO=100


# Settings for audio files
# Audio file counter
file_counter = 1

# 10 +/- seconds for one file
duration = 20 # in seconds

# Samplerate 
samplerate = 16000

# Audio channels (mono)
channels = 1

# Samplewidth 
samplewidth = 2

# Settings for transcription file 
transcription_file = 'transcription.txt'


# Data to process
global_ndarray = None
audio_ndarray = None

print("[+] Load model:")
model = whisper.load_model(MODEL_TYPE)
print(model)
print("[+] Load model end.")

async def save_audio_to_file():
    global audio_ndarray, samplerate, file_counter, duration
    while True:
        if audio_ndarray is not None and audio_ndarray.size >= duration*samplerate:
            filename = f'recordings_{file_counter}.wav'
            file_counter += 1
            wavfile.write(filename, samplerate, audio_ndarray)
            audio_ndarray = None
            print(f'Saved recording {filename}')
        await asyncio.sleep(duration)


def signal_handler(sig, frame):
    print('\nInterrupted, saving last recording...')
    global audio_ndarray, samplerate, file_counter
    if audio_ndarray is not None:
        filename = f'recordings_{file_counter}.wav'
        file_counter += 1
        print(f'Saved last recording {filename}')
        wavfile.write(filename, samplerate, audio_ndarray)
        print("Done.")
    sys.exit(0)


async def inputstream_generator(): 
    global samplewidth, samplerate, channels, BLOCKSIZE
    """Generator that yields blocks of input data as NumPy arrays."""
    q_in = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def callback(indata, frame_count, time_info, status):
        loop.call_soon_threadsafe(q_in.put_nowait, (indata.copy(), status))

    stream = sd.InputStream(samplerate=samplerate, channels=channels, dtype='int16', blocksize=samplerate*duration, callback=callback)
    with stream:
        while True:
            indata, status = await q_in.get()
            yield indata, status

async def process_audio_buffer():
    global global_ndarray, audio_ndarray, SILENCE_THRESHOLD, SILENCE_RATIO, LANGUAGE, file_counter, transcription_file
    async for indata, status in inputstream_generator():
        if (audio_ndarray is not None):
            audio_ndarray = np.concatenate((audio_ndarray, indata), dtype='int16')
        else:
            audio_ndarray = indata
        
        indata_flattened = abs(indata.flatten())
        # discard buffers that contain mostly silence
        if(np.asarray(np.where(indata_flattened > SILENCE_THRESHOLD)).size < SILENCE_RATIO):
            continue

        if (global_ndarray is not None):
            global_ndarray = np.concatenate((global_ndarray, indata), dtype='int16')
        else:
            global_ndarray = indata

        # concatenate buffers if the end of the current buffer is not silent
        if (np.average((indata_flattened[-100:-1])) > SILENCE_THRESHOLD/15):
            continue
        else:
            local_ndarray = global_ndarray.copy()
            global_ndarray = None
            indata_transformed = local_ndarray.flatten().astype(np.float32) / 32768.0
            result = model.transcribe(indata_transformed, language=LANGUAGE)
            print(result["text"])

            # write transcription to file
            with open(transcription_file, 'a') as f:
                f.write(result['text'] + '\n')

        local_ndarray = None
        indata_flattened = None

async def main():
    print('\nActivating wire ...\n')
    transcript_task = asyncio.create_task(process_audio_buffer())
    save_audio_task = asyncio.create_task(save_audio_to_file())
    while True:
        await asyncio.sleep(0)
    transcript_task.cancel()
    save_audio_task.cancel()
    try:
        await transcript_task
        await save_audio_task
    except asyncio.CancelledError:
        print('\nwire was cancelled')


signal.signal(signal.SIGINT, signal_handler)
asyncio.run(main())
