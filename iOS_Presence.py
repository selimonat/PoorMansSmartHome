def iOS_Presence(filename):
    """
        Filename is logged device presence data from iOS_Presence.sh.
        Parses the log file and produces a png figure saved in /tmp/device_presence.png
    """
    
    import pandas as pd
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    d          = pd.read_csv(filename,delimiter=" ",names=["selim_laptop","sonja_laptop","selim_phone","sonja_phone","time_sec"],usecols=[1,2,3,4,6])
    d.time_sec = d.time_sec.apply(lambda x: int(x[1:]))
    d["time_hour"] = np.int8(np.floor((d.time_sec%(60*60*24))/(60*60)))
    t = np.unique(d.time_hour)  #possible hours
    T = np.bincount(d.time_hour)#total counts for each hour
    plt.plot(t,np.bincount(d.time_hour,d.selim_laptop)/T,'red',       #proportion of counts where device is active.
             t,np.bincount(d.time_hour,d.selim_phone)/T,'darksalmon',
             t,np.bincount(d.time_hour,d.sonja_laptop)/T,'blue',
             t,np.bincount(d.time_hour,d.sonja_phone)/T,'skyblue')

    # plt.plot(t,np.bincount(d.time_hour,d.sonja2)/T)  
    plt.legend(('SEL_comp','SEL_phone','SON_comp','SON_phone'))
    plt.xlabel('Hours of the day')
    plt.ylabel('p(active | device)')
    plt.savefig('/tmp/device_presence.png')
    plt.show()


