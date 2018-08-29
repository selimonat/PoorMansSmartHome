import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import zscore

from bokeh.plotting import figure, output_file, show 
from bokeh.embed import components
from bokeh.transform import linear_cmap

def df_to_bar(d):
    """
		d is dict form of current_state df.
    """
	for k1 in d.keys():
		for k2 in d[k1].keys():
			for k3 in d[k1][k2].keys():
				script, div = P.df_to_bar()
				d[k1][k2][k3].update({'div': div})
				d[k1][k2][k3].update({'script': script})
	return d

def df_to_bar():
    """
        data is a dict with x and y keys.
    """

    #output_file = "/tmp/page.html"
    p = figure(tools="pan,box_zoom,reset,save",
               title="test",
               x_axis_label="x",
               y_axis_label="y",
               plot_width=800,
               plot_height=200,            
               x_axis_type="datetime")
    p.grid.visible=False
    X=[1,2,3,4]
    Y=[3,4,5,6]
    p.vbar(x=X,
           top=Y,
           width=1,
           bottom=0,
           color="black")
           #fill_color=linear_cmap(Y,'Viridis256',0,max(Y)),
          #)

    script, div = components(p)
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
   
