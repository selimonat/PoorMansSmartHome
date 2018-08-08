import pandas as pd
import numpy as np
from PoorMansSmartHome import Plotter as pl

class Home:
    def __init__(self):
        self.file_device_log     = "/home/pi/device_presence.log" 
        self.file_human_presence = "/home/pi/human_presence.log" 
        self.file_mic_log        = "/home/pi/mic.log" 
        self.file_ikea_log       = "/home/pi/ikea_lamps.log" 
        #self.log                 = {"device" : d,"human":[d]} 
        self.file_google_history = '/home/pi/MapHistory//Takeout/Location History/Location History.json'
        self.file_google_labels  = '/home/pi/MapHistory/Takeout/Maps/My labeled places/Labeled places.json'
    
    def get_plots(self):
        """
        Exports a set of plots fom ikea, device and mic logs.
        """       
        df = self.get_ikea_log() 
        cols = [2,5,8,11,14,17]
        pl.plot_log(df,cols,"/tmp/ikea_lamp_state.png")      
        
        df = self.get_device_log()
        pl.plot_log(df,'all',"/tmp/device_log.png")
        
        df = self.get_mic_log()
        pl.plot_log(df,'all',"/tmp/mic_log.png",normalize=True)

    def get_device_log(self):
        """
        Reads the device log by Logger.log_device()
        Adds a new column indicating the hour of the day.
        """
        d                        = pd.read_csv(self.file_device_log,delimiter=" ",names=["selim_laptop","sonja_laptop","selim_phone","sonja_phone","time_sec"],usecols=[1,2,3,4,6])
        d.time_sec               = d.time_sec.apply(lambda x: int(x[1:])) #remove the @ sign
        d                        = AttributeAdd(d)
        return d
    def get_mic_log(self):
        """
        reads mic log
        """
        df          = pd.read_csv(self.file_mic_log,sep=' ',header=None,names=["freq_{}".format(f) for f in range(16)] + ["time_sec"])
        df.time_sec = df.time_sec.astype('int64')
        df          = AttributeAdd(df)
        return df
    def get_location_history(self,delta=(0.001,0.002)):
        '''
            Computes a binary home presence vector based on data logged in google map and 
            coordinates of home.
            LocationHistory and LabeledPlaces can be both downloaded from Google Servers.
            Delta (latitude, longitude) defines spatial extend where a point is considered as "at_home".
            Returns a DataFrame object containing all history data together with the at_home state vector.
        '''
        import json
        
        #extract home latitude and longitude from the homefile (assumes you labeled home as Home)
        with open(self.file_google_labels) as json_data:
            locations = json.load(json_data)
        home_latitude, home_longitude =  [j for i in locations["features"] if i['properties']['name']=='Home' for j in i["geometry"]["coordinates"]]
    
        #load geo-history data
        with open(self.file_google_history) as json_data:
            list = json.load(json_data)
        df = pd.DataFrame(list['locations'])
        df["latitude"]  = df.latitudeE7/10000000
        df["longitude"] = df.longitudeE7/10000000
        df['timestamp'] = df.timestampMs.apply(lambda x: int(round(float(x)/1000)))
        df.drop(["longitudeE7","latitudeE7","timestampMs"],axis=1,inplace=True)    
        
        #compute binary state vector of home presence.
        df["at_home"] = (df.latitude > home_latitude-delta[0]) & (df.latitude < home_latitude+delta[0]) & (df.longitude > home_longitude-delta[0]) & (df.longitude < home_longitude+delta[0])
        df            = AttributeAdd(df)
        return df
    
    def get_ikea_log(self):
        """
        Reads the lamp log.
        """
        d = pd.read_csv(self.file_ikea_log,header=None,delimiter=" ",usecols=list(range(0,24)) + [31])
        d = d.astype(np.float64).values
    
        time      = d[:,-1]
        time_bin  = np.int8(np.floor((time % (60*60*24))/(60*60)))  #time bin
        lamps     = np.unique(d[:,list(range(0,21,4))])
        lampdata = dict()
        for lamp in lamps:
            i                   = d == lamp
            dummy               = np.array([d[np.roll(i,shift) == True] for shift in range(1,4)])
            lampdata[str(int(lamp))] = pd.DataFrame({"brightness":dummy[0,],"hue":dummy[1,],"state":dummy[2,]})
        lamp_df = pd.concat(lampdata,axis=1)
        lamp_df["time_sec"] = time
        lamp_df = AttributeAdd(lamp_df)
        return lamp_df
    
    def at_home(self,df):
        '''
            Will add the at_home column to a DF by comparing its epoch time to location history
        '''
        at_home            = []
        human              = self.get_location_history() 
        geo_start,geo_stop = human.timestamp.min(), human.timestamp.max()
        
        i                  = df.time_sec.apply((lambda x,y: np.argmin(np.abs(x-y)) if (x>geo_start)&(x<geo_stop) else None),y=human.timestamp )
        df["at_home"] = human.at_home[i].values
        return df

def AttributeAdd(df):
    
    df["hours"]   = list(df.time_sec.apply(lambda x: np.floor( (x / 3600)      % 24    )))  # hours of the day
    df["days"]    = list(df.time_sec.apply(lambda x: np.floor( (x / (3600*24))         )))  # days of the week
        
    return df

def merge_log(log1,log2,res=60):
    """
        Aligns two dataframes at a resolution of RES.
        Uses epoch time columns of both DataFrames
        Default resolution is in minutes, all data in the same minute
        after epoch time is considered to belong together and merged.
    """
    log1["merger"] = log1.time_sec.apply(lambda x:x//res) 
    log2["merger"] = log2.time_sec.apply(lambda x:x//res) 
    
    return pd.merge( log1 , log2 , on = ['merger'] )
       
def EpochConverter(serie,to):
    """
    Converts linux epoch time to TO.

    TO is fed to time.strftime():
    %Y  Year with century as a decimal number.
    %m  Month as a decimal number [01,12].
    %d  Day of the month as a decimal number [01,31].
    %H  Hour (24-hour clock) as a decimal number [00,23].
    %M  Minute as a decimal number [00,59].
    %S  Second as a decimal number [00,61].
    %z  Time zone offset from UTC.
    %a  Locale's abbreviated weekday name.
    %A  Locale's full weekday name.
    %b  Locale's abbreviated month name.
    %B  Locale's full month name.
    %c  Locale's appropriate date and time representation.
    %I  Hour (12-hour clock) as a decimal number [01,12].
    %p  Locale's equivalent of either AM or PM.
    """
    import time
    return serie.apply( lambda x,to: time.strftime(to,time.gmtime(x)),to=to)

        


