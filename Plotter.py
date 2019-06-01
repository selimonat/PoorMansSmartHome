import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import zscore

from bokeh.plotting import figure, output_file, show 
from bokeh.embed import components
from bokeh.transform import linear_cmap
from bokeh.models.sources import ColumnDataSource


def df_to_bar(df):
    """
        d is dict form of current_state df.
    """
    data = ColumnDataSource(df.filter(like='state'))   
    K    =list(data.data.keys())
    P    = []
    for k in K:
        p = figure(tools="pan,box_zoom,reset,save",
               title=k,
               x_axis_label="time",
               y_axis_label="",
               plot_width=400,
               plot_height=200,            
               x_axis_type="datetime",
                y_axis_location='right',
                  toolbar_location='above')
        p.vbar('second',30*1000,k,
           bottom=0,
           color="black",
           source=data)
        P.append(p)
    script, div = components(P)
    div         = dict(zip(K,div))
    return script, div

def historical_viewa(current_state):
    colors = ["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41", "#550b1d"]
    TOOLS = "hover,save,pan,box_zoom,reset,wheel_zoom"
    
    p = figure(title="US Unemployment ({0} - {1})".format(years[0], years[-1]),
           x_range=years, y_range=list(reversed(months)),
           x_axis_location="above", plot_width=900, plot_height=400,
           tools=TOOLS, toolbar_location='below',
           tooltips=[('date', '@Month @Year'), ('rate', '@rate%')])


def df_to_histogram(df,cols="all",normalize=False):
    """
    counts average state of device in DF for each hour of day.
    """
    #dft       = df.index
    #df        = df.filter(regex="^((?!time_*).)*$")

    #bins to hours
    t              = np.unique(df.index.hour)                        #possible hours
    T              = np.bincount(list(df.index.hour.values))                      #total counts for each hour
    
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
        D = df[col].dropna()
        h.update({col:{"x":t,"y":np.bincount(list(D.index.hour),D)/T}})
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
   
