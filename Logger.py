log_filename_audio = "/home/pi/mic.log"
fft_N              = 16
audio_duration     = 5 #seconds
sampling_rate      = 44100 #Hz
NyquistFreq        = sampling_rate/2
from numpy import savetxt, linspace, round
import subprocess
import time as t

#!/home/pi/miniconda3/envs/py36/bin/python
from goprocam import constants;
from goprocam import GoProCamera;
import time
import subprocess
import os
import cv2
import numpy as np
import sys

import logging
logging.basicConfig(filename='/home/pi/motion_detection.log',level=logging.DEBUG,format='%(message)s')

def log_motion():
    #open camera and change photo mode to smallest size
    gpCam = GoProCamera.GoPro(constants.auth)
    gpCam.sendCamera(constants.Hero3Commands.PHOTO_RESOLUTION,constants.Hero3Commands.PhotoResolution.PR5MP_W)
    
    save_path = "/home/pi/code/python/homeserver/static/%s.JPG"
    #take two pictures in 10 seconds, save them as /tmp/{0,1}.jpg
    filename = [None];
    for i in [0, 1]:
        filename.append(save_path % (i))
        print("Taking photo %d called %s" % (i, filename[-1]))
        gpCam.take_photo()
        time.sleep(2)
        print("Downloading photo %d" % i)
        gpCam.downloadLastMedia(custom_filename=str(filename[-1]))
        print("Reading photo %d" % i)
        img = cv2.imread(filename[-1],cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img,None,fx=.25,fy=.25,interpolation=cv2.INTER_AREA)
        cv2.imwrite(filename[-1],np.uint8(img),[int(cv2.IMWRITE_JPEG_QUALITY), 10])
        #print("Zscoring photo %d" % i)
        #img = (img-np.mean(img))/np.std(img)
        if i == 0:
            out = np.float32(img)
        else:
            out  = out - img
        time.sleep(3)
        
    if len(gpCam.listMedia(format=True, media_array=True)) > 150:
        print('Will now delete all photos')
        gpCam.delete("all")
    
    #compute the absolute diffference between two images
    print("Computing motion power")
    out = abs(out);

    print("Smoothing motion power")
    out = cv2.GaussianBlur(out,(61,61),25)
    motion_power = np.amax(out)
    out = out/np.amax(out)
    out = out*255

    print("Saving diff image")
    filename.append(save_path % "motion_energy")
    cv2.imwrite(filename[-1],np.uint8(out),[int(cv2.IMWRITE_JPEG_QUALITY), 10])
    
    print("Motion Value: %s" % (motion_power))
    #log motion power with time stamp
    out = str(motion_power) + " " + str(time.strftime("%a %d %b %H:%M:%S CET %Y")) + " " + str(round(time.time()))
    logging.info(out)

    #print("Montage collected data")
    #cmd = "/usr/bin/montage %s %s %s -geometry +0+0 -resize 25%% -background none  %s" % (filename[1],filename[2],filename[3],filename[3])
    #cmd = cmd.split()
    #time.sleep(2)
    #subprocess.call(cmd)

    #if motion_power > 30:
    #   print("sending results as an email")
    #   subprocess.Popen(["/home/pi/code/shell/bin/SendLastPic.sh","/home/pi/motion_detection/","Motion value: " + str(motion_power),"Motion Detected (>20)","onatselim@gmail.com"])
    
    return motion_power

def sql_audio():
    from scipy.fftpack import rfft
    import time, os
#    #get spectrum   
    fft_N              = 8
    _,signal_time =  record_sound()
    signal      = wav_to_float()
    y_hat       = abs(rfft(signal,fft_N)) ** 2
    freq        = round(linspace(0,1,fft_N/2+1)*NyquistFreq)
    freq        = [int(f) for f in freq]
    data        = list(zip(freq,y_hat))
    #export it to table (this could be fun later)
    import MySQLdb
    import subprocess
    db = MySQLdb.connect("localhost", "selim", "password", "devices")
    curs=db.cursor()

    query = """INSERT INTO log_mic(freq,power) values (%s,%s)"""
    curs.executemany(query,data)
    db.commit()
    
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

