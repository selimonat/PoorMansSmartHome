# PoorMansSmartHome

This is currently a work-in-progress hobby package that aims to bring some intelligent behavior in the living room. 
By intelligent, what is meant is controlling lights in the living room in at least one sensible manner based on some variables. 
For example, dimming lights depending on time of the night when you are alone at home, but not doing so when there are visitors.
This program is supposed to run in a device that is constantly ON, in order to collect information.

Collected variables include presence of personal electronic devices such as smartphones and laptops, but includes also
microphone activity, ikea motion sensors, pictures taken regularly from an old GoPro camera and finally the state of 
ikea light bulbs. These variables are assembled together in order to predict human presence, number of humans currently present,
number of visitors. And ultimately, depending on these predictions and the time of the day different light programs will be 
triggered.

Road Maps in Poor Man's Smart Home:

(1) The first part of this project deals with the problem of inferring a binary representation of current human presence. 
The progress in this direction is being documented in the following [Jupyter Notebook](https://github.com/selimonat/JupyterNotebooks/blob/master/DevicePresence/Device%20Presence%20Analysis.ipynb).

(2) Once this is achieved with a given accuracy level, light control will need to be implemented.

(3) In the long term, this algorithm will need to keep learning from novel situations or repeat less mistakes.
