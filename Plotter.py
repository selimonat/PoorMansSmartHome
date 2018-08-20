import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import zscore

from bokeh.plotting import figure, output_file, show 
from bokeh.embed import components

def df_to_histogram(df,cols="all",normalize=False):
    """
    counts average state of device in DF for each hour of day.
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
    
    #for each column compute histogram
    h = dict()
    for col in cols:
        if normalize is True:
            df[col] = (df[col] - df[col].mean())/df[col].std(ddof=0)
        h.update({col:{"x":t,"y":np.bincount(list(dft.time_hour),df[col])/T}})
    return h

def histogram_to_plot(H):
    """
        plots the histogram, returns JS script and html div tag to be 
        inserted in the html file
    """
    P = []
    for h in H:
        title = 'y = f(x)'
        plot = figure(title= title , 
            x_axis_label= 'X-Axis', 
            y_axis_label= 'Y-Axis')
        for k,v in h.items():
            plot.line(v["x"], v["y"], legend= 'f(x)', line_width = 2)
        #Store components 
        P.append(plot)
    script, div = components(P)
    return script, div
   
