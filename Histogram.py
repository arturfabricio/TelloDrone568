import scipy
import imageio
import scipy.misc
from scipy import ndimage
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
from scipy import misc

img = imageio.imread("1.png")
array=np.asarray(img)
arr=(array.astype(float))/255.0
img_hsv = colors.rgb_to_hsv(arr[...,:3])

lu1=img_hsv[...,0].flatten()
plt.subplot(1,3,1)
plt.hist(lu1*360,bins=360,range=(0.0,360.0),histtype='stepfilled', color='r', label='Hue')
plt.title("Hue")
plt.xlabel("Value")
plt.ylabel("Frequency")
plt.axvline(0, color='black',linewidth=3)
plt.axvline(110, color='black',linewidth=3)
axes = plt.gca()
axes.set_ylim([0,30000])
plt.legend()

lu2=img_hsv[...,1].flatten()
plt.subplot(1,3,2)                  
plt.hist(lu2,bins=100,range=(0.0,1.0),histtype='stepfilled', color='g', label='Saturation')
plt.title("Saturation")   
plt.xlabel("Value")    
plt.ylabel("Frequency")
plt.axvline(0, color='black',linewidth=3)
plt.axvline(0.43, color='black',linewidth=3)
axes = plt.gca()
axes.set_ylim([0,15000])
plt.legend()

lu3=img_hsv[...,2].flatten()
plt.subplot(1,3,3)                  
plt.hist(lu3*255,bins=256,range=(0.0,255.0),histtype='stepfilled', color='b', label='Intesity')
plt.title("Intensity")   
plt.xlabel("Value")    
plt.ylabel("Frequency")
plt.axvline(0, color='black',linewidth=3)
plt.axvline(110, color='black',linewidth=3)
axes = plt.gca()
axes.set_ylim([0,8000])
plt.legend()
plt.show()