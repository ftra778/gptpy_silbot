from google.cloud import speech
import io
import os
import time
import sys
import re
import socket
import subprocess
from pydub import AudioSegment


os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'/home/user1/stable-device-428323-i4-0376f5bec9c6.json'


def run_quickstart(audio) -> speech.RecognizeResponse:
    # Instantiates a client
    client = speech.SpeechClient()
    audio_list = [audio]
    
    requests = (
        speech.StreamingRecognizeRequest(audio_content=chunk) for chunk in audio_list
    )

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=48000,
        language_code="en-US",
    )

    streaming_config = speech.StreamingRecognitionConfig(config=config)

    # streaming_recognize returns a generator.
    responses = client.streaming_recognize(
        config=streaming_config,
        requests=requests,
    )
    
    for response in responses:
        for result in response.results:
            alternatives = result.alternatives
            for alternative in alternatives:
                # print(f"Transcript: {alternative.transcript}")
                sttresult = alternative.transcript
                
    print(sttresult)
    return sttresult

if __name__ == "__main__":
    audio = b''
    i = 0
    print("Connecting to stt server...")
    (HOST,PORT) = ('192.168.0.100', 6644)
    sttclient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sttclient.connect((HOST,PORT))
    print("Connected to " + HOST + " at port " + str(PORT))
    print("Connecting to gpt server...")
    (HOST,PORT) = ('192.168.0.100', 7789)
    gptclient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    gptclient.connect((HOST,PORT))
    print("Connected to " + HOST + " at port " + str(PORT))

    while True:
        while True:
            print(i)
            i = i + 1
            buf = sttclient.recv(1024)
            audio += buf
            if audio[-17:] == b'ENDOFTRANSMISSION':
                break
        print("Received")
        sendto = run_quickstart(audio[:-17])
        buf = b''
        audio = b''
        gptclient.sendall(sendto.encode('utf8'))
        gptclient.recv(1024)
        sttclient.sendall(b'0')
    client.close()
    # run_quickstart(audio)
    # client.sendall("0")

                                                                      
