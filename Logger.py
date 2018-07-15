log_filename_audio = "/home/pi/mic.log"
fft_N              = 16
audio_duration     = 5 #seconds
sampling_rate      = 44100 #Hz
NyquistFreq        = sampling_rate/2
from numpy import savetxt, linspace, round
import subprocess
import time as t

def log_audio():
    """ Takes a snapshot of the auditory landscape, computes its Fourier
    transform, and saves the result to the log file with its time stamp. 
    """
    from scipy.fftpack import rfft
    import time, os
    
    _,signal_time =  record_sound()
    signal      = wav_to_float()
    y_hat       = abs(rfft(signal,fft_N)) ** 2
    freq        = round(linspace(0,1,fft_N/2+1)*NyquistFreq)
    if not os.path.exists(log_filename_audio):
        with open(log_filename_audio, "wb") as file:
            savetxt(file, freq[0:-1], delimiter=' ', newline=' ')
            savetxt(file,[freq[-1]])

    with open(log_filename_audio, "ab") as file:
        savetxt(file,y_hat, delimiter=' ',newline=' ')
        savetxt(file,[signal_time])

def record_sound():
    """ Triggers ALSA record command to save an auditory snapshot onto 
    a wav file.
    """
    command = "/usr/bin/arecord --device=hw:1,0 --format S16_LE --rate " + str(sampling_rate) + " -c1  -d " + str(audio_duration) + " /tmp/test.wav"  
    #print(command)
    return subprocess.call([command],shell=True), round(t.time())  

def wav_to_float(wave_file="/tmp/test.wav"):
    """ Reads the wav file and converts it to flat
    """
    import wave
    import struct
    import sys
    with wave.open(wave_file) as w:
        astr = w.readframes(w.getnframes())
    
    # convert binary chunks to short 
    a = struct.unpack("%ih" % (w.getnframes()* w.getnchannels()), astr)
    a = [float(val) / pow(2, 15) for val in a]
    return a

def log_device():
    """ Pings devices, saves the result to a log file.
    """
    command = "/home/pi/code/shell/bin/iOS_Presence_Logger.sh"
    return subprocess.call([command],shell=True), round(t.time()) 
