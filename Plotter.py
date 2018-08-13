import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import zscore

def plot_log_shaded(df):
    '''
        Plots log
    '''   
    #for g in df.groupby(['days']):
    #    plot(

def plot_log(df,cols="all",output_file=None,normalize=False):
    """
    plots the log and optinally saves the figure. 
    maps all log values to either of the 24 possible hours.
    plots the average of log value in that bin.
    """
    dft       = df.filter(like="time_")
    df        = df.filter(regex="^((?!time_*).)*$")

    #bins to hours
    t              = np.unique(dft.time_hour)                        #possible hours
    T              = np.bincount(list(dft.time_hour))                      #total counts for each hour
    
    #take either all or selected columns
    if cols is "all":
        cols           = df.columns
    else:
        cols           = df.columns[cols]
    #plot columns except the time stamp column, and z-score transform if required.
    plt.close()
    plt.figure(figsize=(4.5,4.5))
    for col in cols:
        if normalize is True:
            df[col] = (df[col] - df[col].mean())/df[col].std(ddof=0)
        color = tuple(map(tuple,np.random.rand(1,3)))[0]
        plt.plot(t,np.bincount(list(dft.time_hour),df[col])/T ,'.-',markersize=10)   #proportion of counts where device is active.
    plt.legend(cols)
    plt.xticks(np.arange(min(t),max(t),3))
    ax = plt.gca()
    ax.grid(which='major', axis='x', linestyle='--')
    if output_file is not None:
       print('will print something')
       plt.savefig(output_file,dpi=100,transparent=True)
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
