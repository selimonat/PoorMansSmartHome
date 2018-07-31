import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import zscore

def plot_log(df,cols="all",output_file=None,normalize=False):
    """
    plots and optinally saves the log after binning epoch second onto hours of the day.
    """
    #hours   = list(df.time_sec.apply(lambda x: np.floor(x % (3600*24*7) / (3600*24))))
        
        
    hours   = list(df.time_sec.apply(lambda x: np.floor(x % (3600*24) / (3600))))
    t              = np.unique(hours)                        #possible hours
    T              = np.bincount(hours)                      #total counts for each hour
    
    if cols is "all":
        cols           = df.columns
    else:
        cols           = df.iloc[:,cols]

    plt.close()
    for col in cols:
        if col != "time_sec":
            if normalize is True:
                df[col] = (df[col] - df[col].mean())/df[col].std(ddof=0)
            color = tuple(map(tuple,np.random.rand(1,3)))[0]
            plt.plot(t,np.bincount(hours,df[col])/T ,'.-',markersize=10)   #proportion of counts where device is active.
    plt.legend(cols)
    plt.xticks(np.arange(min(t),max(t),3))
    ax = plt.gca()
    ax.grid(which='major', axis='x', linestyle='--')
    if output_folder is not None:
       plt.savefig(output_file)
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
