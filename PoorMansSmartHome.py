import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def plotlog_iOS_Presence(log_file="/home/pi/device_presence.log",output_folder='/home/pi/code/python/homeserver/static/'):
    """
        (log_file) is logged device presence data from iOS_Presence.sh.
        Parses the log file and produces a png figure saved in /tmp/device_presence.png
    """
    

    d              = pd.read_csv(log_file,delimiter=" ",names=["selim_laptop","sonja_laptop","selim_phone","sonja_phone","time_sec"],usecols=[1,2,3,4,6])
    d.time_sec     = d.time_sec.apply(lambda x: int(x[1:]))
    d["time_hour"] = np.int8(np.floor((d.time_sec%(60*60*24))/(60*60)))
    t              = np.unique(d.time_hour)  #possible hours
    T              = np.bincount(d.time_hour)#total counts for each hour
    plt.plot(t,np.bincount(d.time_hour,d.selim_laptop)/T,'red',       #proportion of counts where device is active.
             t,np.bincount(d.time_hour,d.selim_phone)/T,'darksalmon',
             t,np.bincount(d.time_hour,d.sonja_laptop)/T,'blue',
             t,np.bincount(d.time_hour,d.sonja_phone)/T,'skyblue')

    # plt.plot(t,np.bincount(d.time_hour,d.sonja2)/T)  
    plt.legend(('SEL_comp','SEL_phone','SON_comp','SON_phone'))
    plt.xlabel('Hours of the day')
    plt.ylabel('p(active | device)')
    plt.savefig(output_folder + 'device_presence.png')
    plt.show()

def plotlog_ikea_lamp(filename="/home/pi/ikea_lamps.log",output_folder='/home/pi/code/python/homeserver/static/'):
    '''
        parses log file (filename), returns state, brightness and hue of 6
        lamps as a dict with lamp numbers.
        {lamp_number:{brightness:X,hue:Y}}
    '''
    d = pd.read_csv(filename,delimiter=" ",usecols=list(range(0,24)) + [31])
    d         = d.astype(np.float64).values
    
    time      = d[:,-1]
    time_bin  = np.int8(np.floor((time % (60*60*24))/(60*60)))  #time bin
    lamps     = np.unique(d[:,list(range(0,21,4))])
    final     = dict();
    for lamp in lamps:
        i               = d == lamp
        lamp_data       = np.array([d[np.roll(i,shift) == True] for shift in range(1,4)])
        state           = lamp_data[2,:]
        all_count       = np.bincount(time_bin)
        active_count    = np.bincount(time_bin,state)
        brightness      = np.bincount(time_bin,state*lamp_data[0,:])/active_count
        hue             = np.bincount(time_bin,state*lamp_data[1,:])/active_count    
        final.update({int(lamp):{"hue":hue,"brightness":brightness,"state":active_count/all_count}})
        plt.figure(1)       
        plt.subplot(3,1,1)
        plt.title(lamp)
        plt.plot( final[lamp]["state"] )
        
        plt.subplot(3,1,2)
        plt.plot( final[lamp]["brightness"] )
        
        plt.subplot(3,1,3)
        plt.plot( final[lamp]["hue"] )
        
        plt.savefig(output_folder + 'lamp_stats_' + str(int(lamp)) + '.png')
        plt.close(1)

    return final
