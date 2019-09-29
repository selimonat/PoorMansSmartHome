import pandas as pd
import numpy as np
from PoorMansSmartHome import Plotter as pl

from goprocam import constants;
from goprocam import GoProCamera;

import time
import subprocess

class Home:
    def __init__(self):
        self.file_device_log     = "/home/pi/device_presence.log" 
        self.file_human_presence = "/home/pi/human_presence.log" 
        self.file_motion_log     = "/home/pi/motion_detection.log" 
        self.file_mic_log        = "/home/pi/mic.log" 
        self.file_light_log       = "/home/pi/ikea_lamps.log" 
        self.visual_save_path    = "/home/pi/getvisuals_log/"
        #self.log                 = {"device" : d,"human":[d]} 
        self.file_google_history = '/home/pi/MapHistory//Takeout/Location History/Location History.json'
        self.file_google_labels  = '/home/pi/MapHistory/Takeout/Maps/My labeled places/Labeled places.json'
        
        self.length_device_log     = self.LogLength(self.file_device_log)
        self.length_mic_log        = self.LogLength(self.file_mic_log)
        self.length_light_log       = self.LogLength(self.file_light_log)
    def get_log(self,log_name):
        """
        Gets the log file of various sources.
        """
        method_name = 'get_' + str(log_name) + '_log'
        method = getattr(self, method_name, lambda: "Invalid log name")
        return method(last_row=60*24*5) #limit to last 50 days

    def get_plot(self,log_name):
        """
        Exports a set of plots fom light, device and mic logs.
        """       
        script_div = ()
        df = self.get_log(log_name)                        
 
        P = [ pl.df_to_histogram(df[ df.index.day == df.index.day.max()]),
              pl.df_to_histogram(df[ df.index.week == df.index.week.max()]),
              pl.df_to_histogram(df[ df.index.month == df.index.month.max()]), 
              pl.df_to_histogram(df)
             ]
 
        script,div = pl.histogram_to_plot((tuple(P)))
        return script,div

    def get_device_log(self,last_row=0):
        """
        Reads the device log by Logger.log_device()
        Adds a new column indicating the hour of the day.
        Use rows to import only ROWS amount of lines from the tail of the log file.
        1 would read only the last log item.
        """
        
        if last_row != 0:
            last_row = self.LogLength(self.file_device_log) - last_row #number of rows to be skipped.
    
        d                        = pd.read_csv(self.file_device_log,delimiter=" ",names=["selim_laptop","sonja_laptop","selim_phone","sonja_phone","second"],usecols=[1,2,3,4,6],skiprows=last_row)
 
        d                        = add_index(d)
        d.columns                = pd.MultiIndex.from_product([['device_presence'],d.columns,['state']],names=["log_type","source","attribute"])
        return d

    def get_motion_log(self,last_row=0):
        """
        reads motion log.
        """
        if last_row != 0:
            last_row = self.LogLength(self.file_motion_log) - last_row #number of rows to be skipped.
        
        df = pd.read_csv(self.file_motion_log,header=None,delimiter=' ',usecols=[0,7],names=["motion","second"],skiprows=last_row)
        df                       = add_index(df)
        df.columns               = pd.MultiIndex.from_product([['motion'],df.columns,['state']],names=["log_type","source","attribute"])
        return df
    def get_mic_log(self,last_row=0):
        """
        reads mic log
        """
        if last_row != 0:
            last_row = self.LogLength(self.file_mic_log) - last_row #number of rows to be skipped.
        #load log file
        df             = pd.read_csv(self.file_mic_log,sep=' ',header=None,names=["freq_{}".format(f) for f in range(16)] + ["second"],skiprows=last_row)
        #remove zero freq, not interesting
        #df             = df.drop('freq_0',axis=1)
        #collapse power across frequencies
        data_cols      = df.filter(like='freq_').columns[1::2]
        #df["power"]    = -np.log10(df[data_cols].sum(axis=1))
        #df["power"]    = -np.log10(df[data_cols].sum(axis=1))
        #zscore transformation on power (causes an obvious problem when only one row is asked for)
        #df["power"]  = df["power"].apply(lambda x: (x-np.mean(x))/np.std(x))
        #remove all freq channels
        df             = df.drop(data_cols,axis=1)
        df             = add_index(df)
        #df             = df.apply(lambda x: -np.log10(x))
        df.columns     = pd.MultiIndex.from_product([['mic'],df.columns,['state']],names=["log_type","source","attribute"])
        return df
    def get_light_log(self, last_row=0):
        """
        Reads the lamp log.
        """
        if last_row != 0:
            last_row = self.LogLength(self.file_light_log) - last_row #number of rows to be skipped.
        d = pd.read_csv(self.file_light_log,
                        index_col=4,
                        header=None,
                        delimiter="\t",
                        names=['source','brightness','color','state'],
                        dtype={0:'category',1:'uint8',2:'float',3:'uint8'},
                        skiprows=last_row
                       )
        d['time'] = d.index
        d["log_type"] = "light_log"
        d.set_index(keys=['time','source','log_type'],inplace=True)
        d = d.loc[~d.index.duplicated(keep='first')]
        d = d.stack(dropna=False).unstack(level=[2,1,3])
        d.columns.rename('attribute',level=2,inplace=True)
        d.index = pd.to_datetime(d.index,unit='s')
        return d
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
        df            = add_index_attribute(df)
        return df
    
    
    def at_home(self,df):
        '''
            Will add the at_home column to a DF by comparing its epoch time to location history
        '''
        at_home            = []
        human              = self.get_location_history() 
        geo_start,geo_stop = human.timestamp.min(), human.timestamp.max()
        
        i                  = df.second.apply((lambda x,y: np.argmin(np.abs(x-y)) if (x>geo_start)&(x<geo_stop) else None),y=human.timestamp )
        df["at_home"] = human.at_home[i].values
        return df

    def LogLength(self,filename):
        '''
        Returns number of lines in a filename
        '''
        import subprocess
        ps = int(subprocess.check_output('cat ' + filename +  ' | wc -l',shell=True))
        return ps

    def CurrentState_as_df(self,last_row=1):
        '''
        Returns the latest states of devices.
        '''
        out = list()
        df  = self.get_device_log(last_row=last_row)
        out.append(df)
        
        #df    = self.get_mic_log(last_row=last_row)
        #out.append(df)

        #df    = self.get_light_log(last_row=last_row)
        #out.append(df)

        #df            = self.get_motion_log(last_row=last_row)
        #out.append(df)
        
        return join_log(out)

    def CurrentState(self,last_row=1):
        '''
        Returns the latest states of devices.
        '''
        out = dict()
        df    = self.get_device_log(last_row=last_row)
        out["device"] = df.to_dict(orient='list')
        
        df    = self.get_mic_log(last_row=last_row)
        out["mic"] = df.to_dict(orient='list')

        df    = self.get_light_log(last_row=last_row)      
        df.columns = df.columns.get_level_values(0)
   
        out["light"] = df.to_dict(orient='list')

        df            = self.get_motion_log(last_row=last_row)
        out["motion"] = df.filter(regex="^((?!time_*).)*$").to_dict(orient='list')
        
        out["file"] = {"home_visual":"0.JPG","motion_energy" : "motion_energy.JPG"}  
        return out
    def take_a_photo(self):
        gpCam = GoProCamera.GoPro(constants.auth)
        gpCam.take_photo(1)
        time.sleep(2)
        save_path  = self.visual_save_path
        filename   = save_path + str(round(time.time())) + ".jpg"
        gpCam.downloadLastMedia(custom_filename=filename)
        
        #print("resizing image to 50%")
        #subprocess.call(["/usr/bin/convert {} -resize 25% {}".format(filename,filename)],shell=True)
        #print("sending results as an email")
        #subprocess.Popen(["/home/pi/code/shell/bin/SendLastPic.sh","/home/pi/getvisuals_log/","'Email sent by GetVisual.py'","Visual from your home", "onatselim@gmail.com"])

def add_index(d):
        """
            transforms epoch second to DatetimeIndex after rounding to minutes
            and possibly removing the @ char. Removes any duplicate indices.
        """
        #if second has an at sign remove it
        try: 
            if d.second.at[0][0] == '@':
                d.second = d.second.apply(lambda x: x[1:])
        except:
            pass
        
        #round it to minute and use it as index
        d.index                  = pd.to_datetime(d.second.apply(lambda x:
                                                    int(x) // 60 * 60 ), 
                                                    unit="s")
        #remove the second column
        d.drop("second",inplace=True,axis=1)
        
        #remove possible duplicate indices
        di = d.index.duplicated()
        if sum(di) > 0:
            print('Warning: {} duplicate indices are removed'.format(sum(di)))
            d  = d[~di]

        #fill with NaN if log is missing
        d = d.asfreq('1Min')
        return d

def add_index_attribute(df):
    """
        uses available time information which is in the form of epoch seconds,
        and develops novel attributes. Obsolet since I started using datatime
        objects as df index.
    """
    df["hour"]   = list(df.second.apply(lambda x: int(np.floor( (x / 3600)      % 24    ))))  # hours of the day
    df["month"]    = list(df.second.apply(lambda x: int(np.floor( (x / (3600*24*30))         ))))  # days of the week
    df["week"]    = list(df.second.apply(lambda x: int(np.floor( (x / (3600*24*7))         ))))  # days of the week
    df["day"]    = list(df.second.apply(lambda x: int(np.floor( (x / (3600*24))         ))))  # days of the week
    df.set_index(["second","hour","month","week","day"],inplace=True)
        
    return df

def tuplekey_to_nested(d):
    """
        takes a dict with keys defined as tuples and returns
        a dict with nested keys.
    """
    #print("=======================\n")
    D = dict()
    S = list(set(map(len,d.keys())))
    if 1 not in S:                              #check whether the size of the tuple key is one
        for k,v in d.items():  
            key_above = k[0:-1]
            key_below = k[-1]                 #run across the MultiIndex
            #print(key_above)
            #print(key_below)
            if key_above not in D:         #create a tuple key based on all keys except the last one.
                D[key_above] = {key_below : v }
            else:       
                D[key_above].update({key_below : v }) 
        return tuplekey_to_nested(D)            #continue doing the same until there is a tuple of size 1 as a key
    else:
        #for a reason I dont quiet understand the last iteration always creates
        #a tuple instead of a string. the bla variable takes care of it until I
        #understand why.
        bla = dict()
        for k,v in  d.items():
            bla[k[0]]=v
        return bla
        return d


def join_log(log):
    """
        Joins a list of dataframes in LOG using their index.
    """
    df0           = log[0]
    for df in log[1:]:
        df0 = df0.join(df,how='outer')
    return df0
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

        


