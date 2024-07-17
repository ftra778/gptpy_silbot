import pyaudio
import wave
from pydub import AudioSegment
import os
import math
import struct
import time
import subprocess
import socket
import sys

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'/home/user1/bold-meridian-424805-n4-e01381bda6ca.json'

# Record audio segment for Speech To Text
class RecordAudio:
    def __init__(self, OUTPUT_FILENAME="gptQuery.wav", CHANNELS=1, RATE=44100, CHUNK=1024, AUDIO_FORMAT=pyaudio.paInt16, INPUT_DEVICE_INDEX=0, VOL_THRESHOLD=0.08, SAMPLE_SIZE=10, IP="localhost", PORT=6644):
        self.audio_format=AUDIO_FORMAT
        self.channels=CHANNELS
        self.rate=RATE
        self.chunk=CHUNK
        self.input_device_index=INPUT_DEVICE_INDEX
        self.owav=OUTPUT_FILENAME if OUTPUT_FILENAME[-4:] is '.wav' else OUTPUT_FILENAME+'.wav'
        self.oflac=OUTPUT_FILENAME if OUTPUT_FILENAME[-5:] is '.flac' else OUTPUT_FILENAME+'.flac'
        self.vol_threshold=VOL_THRESHOLD
        self.sample_size=SAMPLE_SIZE
        self.audio=pyaudio.PyAudio()

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((IP, PORT))
        print("Listening on port " + str(PORT) + "...")
        self.server.listen(1)
        self.conn, addr = self.server.accept()
        print("Connected to " + str(addr))
        
        self.stream=self.audio.open(
                                    format=self.audio_format,
                                    channels=self.channels,
                                    rate=self.rate,
                                    input=True,
                                    frames_per_buffer=self.chunk,
                                    input_device_index=self.input_device_index
                                    #stream_callback=self.audio_callback
                                    )
        self.frames = []

    # Close streams
    def terminate(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        self.server.close()

    # Save audio sample
    def save_sample(self):
        waveFile = wave.open(self.owav, 'wb')
        waveFile.setnchannels(self.channels)
        waveFile.setsampwidth(self.audio.get_sample_size(self.audio_format))
        waveFile.setframerate(self.rate)
        waveFile.writeframes(b''.join(self.frames))
        waveFile.close()
        
        wavtoflac = AudioSegment.from_wav(self.owav)
        wavtoflac.export(self.oflac,format="flac")

        del self.frames[:]
        
    # Send audio data over socket
    def send(self):
        # print(len(self.frames))
        # self.conn.sendall(str(len(self.frames)).encode('utf8'))
        print("Processing...")
        for l in self.frames: 
            self.conn.sendall(l)
        self.conn.sendall(r"ENDOFTRANSMISSION".encode('utf8'))

    def wait(self):
        self.conn.recv(1024)

    # RMS function to accurately detect and compare sound volume
    def rms(self, data):
        count = len(data)/2
        format = "%dh"%(count)
        shorts = struct.unpack(format, data)
        sum_squares = 0.0
        for sample in shorts:
            n = sample * (1.0/32768)
            sum_squares += n*n
        return math.sqrt(sum_squares / count)

    def run(self):
        sample = []         # Sample list to detect long pauses 
        rec_flag = False    # Flag to start recording audio sample
        fin_flag = False    # Flag to finish recording audio sample
        start_buffer = 5    # Buffer to append to start of recording
        finish_buffer = 5   # Buffer to remove the end of recording
        ready = False       # Flag to indicate microphone is ready for input (When starting stream loud static can sometimes be heard)
        curr_time = time.time()
        start_time = time.time()
        print("Warming up, please wait...")
        while ready is False:
            data = self.stream.read(self.chunk, exception_on_overflow=False)
            rmsdata = self.rms(data)
            print("*    " + str(rmsdata))
            if rmsdata < self.vol_threshold:
                ready = True
        print("Ready! Please ask me anything")
        # while ((curr_time-start_time) < 3):
        #     curr_time = time.time()
        #     data = self.stream.read(self.chunk, exception_on_overflow=False)
        #     self.frames.append(data)
        #     print("*    " + str(self.rms(data)))


        while fin_flag is False:
            data = self.stream.read(self.chunk, exception_on_overflow=False)
            if rec_flag is True:
                self.frames.append(data)
                sample.append(data)
                if len(sample) >= finish_buffer * self.sample_size and all(x < self.vol_threshold for x in [self.rms(_) for _ in sample[-self.sample_size:]]):
                    fin_flag = True
                    self.frames = self.frames[:-self.sample_size]
                elif len(sample) >= finish_buffer * self.sample_size:
                    del sample[:]
            
            # Wait until volume threshold is consistently high to begin recording audio
            if rec_flag is False:
                sample.append(data)
                if len(sample) >= start_buffer * self.sample_size and all(x > self.vol_threshold for x in [self.rms(_) for _ in sample[-self.sample_size:]]):
                    print("*    Speech detected")
                    rec_flag = True
                    self.frames.extend([str(_) for _ in sample])
                    del sample[:]
                elif len(sample) >= start_buffer * self.sample_size:
                    del sample[:]
        self.send()        # self.save_sample()
        self.wait()

def subprocess_run(*popenargs, **kwargs):
    input = kwargs.pop("input", None)
    check = kwargs.pop("handle", False)

    if input is not None:
        if 'stdin' in kwargs:
            raise ValueError('stdin and input arguments may not both be used.')
        kwargs['stdin'] = subprocess.PIPE

    process = subprocess.Popen(*popenargs, **kwargs)
    try:
        stdout, stderr = process.communicate(input)
    except:
        process.kill()
        process.wait()
        raise
    retcode = process.poll()
    if check and retcode:
        raise subprocess.CalledProcessError(
            retcode, process.args, output=stdout, stderr=stderr)
    return retcode, stdout, stderr


if __name__ == "__main__":
    recordaudio = RecordAudio(RATE=48000, INPUT_DEVICE_INDEX=9, VOL_THRESHOLD=0.025, SAMPLE_SIZE=10, CHUNK=512, IP="192.168.0.100", PORT=6644)
    while True:
        recordaudio.run()
    recordaudio.terminate()
    
    # user = "silbot3"
    # i = 0
    # OUTPUT_FILENAME = "/home/" + user + "/tts/gptQuery"
    # recordaudio = RecordAudio(RATE=48000, OUTPUT_FILENAME=OUTPUT_FILENAME, INPUT_DEVICE_INDEX=8, VOL_THRESHOLD=0.025, SAMPLE_SIZE=10, CHUNK=512)
    # while True:
    #     recordaudio.run()
    #     # subprocess.run(["scp", "/home/silbot3/tts/gptQuery.flac", "user1@192.168.0.101:/home/user1/silbot_mm/Audio/"])
    #     subprocess_run(["scp", "/home/silbot3/tts/gptQuery.flac", "user1@192.168.0.101:/home/user1/silbot_mm/Audio/"])
    #     time.sleep(5)
    #     prev_audio_mtime = os.stat("/home/silbot3/tts/output.mp3").st_mtime # Record current TTS audio file metadata

    #     # Wait until TTS audio is updated and silbot has finished a motion
    #     while(prev_audio_mtime == os.stat("/home/silbot3/tts/output.mp3").st_mtime):
    #         pass
    #     time.sleep(7)

# def run_quickstart(local_file_path="/home/user1/silbot_mm/Audio/gptQuery.flac") -> speech.RecognizeResponse:
#     # Instantiates a client
#     client = speech.SpeechClient()


#     with io.open(local_file_path, "rb") as f:
#         content = f.read()
#     audio = {"content": content}


#     config = speech.RecognitionConfig(
#         sample_rate_hertz=44100,
#         language_code="en-US",
#     )

#     # Detects speech in the audio file
#     response = client.recognize(config=config, audio=audio)

#     for result in response.results:
#         print(f"Transcript: {result.alternatives[0].transcript}")


# Run using callback function

        # self.audio_queue = Queue.Queue()
    #     self.rec_flag = False
    #     self.fin_flag = False

    # def audio_callback(self, in_data, frame_count, time_info, status):
    #     if self.rec_flag == 1:
    #         self.audio_queue.put(in_data)
    #     if self.fin_flag == 0:
    #         callback_flag = pyaudio.paContinue
    #     else:
    #         callback_flag = pyaudio.paComplete
        
    #     return in_data, callback_flag
    # def run_test(self):
    #     sample = []         # Sample list to detect long pauses 
    #     rec_flag = 0        # Flag to start recording audio sample
    #     fin_flag = 0        # Flag to finish recording audio sample
    #     start_buffer = 3    # Buffer to append to start of recording
    #     finish_buffer = 5   # Buffer to remove the end of recording
    #     ready = False
        
    #     self.rec_flag = 1
    #     while ready is False:
    #         if self.audio_queue.empty() is False:
    #             if self.rms(self.audio_queue.get()) < self.vol_threshold:
    #                 ready = True
    #     print("Recording... Press SPACE to stop")

    #     while True:
    #         try:
    #             # data = self.stream.read(self.chunk, exception_on_overflow=False)
    #            if self.audio_queue.empty() is False: 
    #                 self.frames.append(self.audio_queue.get())
    #                 # sample.append(data)
    #         # Manually terminate recording
    #         except KeyboardInterrupt:
    #             break
    #         if keyboard.is_pressed('space'):
    #             print("Stopping recording after a brief delay")
    #             time.sleep(0.2)
    #             self.fin_flag = 1
    #             break
    #     self.terminate()