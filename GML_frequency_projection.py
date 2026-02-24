from GML import *
import csv
from datetime import datetime
import os
import logging
import sys
import numpy as np
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import time
import tzlocal
import cv2
import scipy.signal
logging.disable(sys.maxsize)
import threading
# Declraing a lock
lock = threading.Lock()

max_phase_history=[]
min1=999999999
max1=0
min2=999999999
max2=0

fig1 = None
ax1=[]
ax2=[]
ax3=[]
polarX=[]
polarY=[]
iteration_count=0

csv_handle2=None

from matplotlib.transforms import Bbox

def full_extent(ax, pad=50.0):
    """Get the full extent of an axes, including axes labels, tick labels, and
    titles."""
    # For text objects, we need to draw the figure first, otherwise the extents
    # are undefined.
    ax.figure.canvas.draw()
    items = ax.get_xticklabels() + ax.get_yticklabels()
#    items += [ax, ax.title, ax.xaxis.label, ax.yaxis.label]
    items += [ax, ax.title]
    bbox = Bbox.union([item.get_window_extent() for item in items])

    return bbox.expanded(1.0 + pad, 1.0 + pad)

def autocorr(x):
    result = np.correlate(x, x, mode='full')
    return result[int(result.size/2):]

def autocorr2d_one_quadrant(x):
    ishape = np.shape(x)
    result = np.array(scipy.signal.correlate2d(x, x, mode='full', boundary='fill', fillvalue=0))
    #Manipulate to return only the top right quandrant of the auto correlation
    top_right = result[:ishape[0],:ishape[1]]
    top_right = np.flip(top_right, axis=0)
    top_right = np.flip(top_right, axis=1)
    return top_right

def autocorr2d(x):
    ishape = np.shape(x)
    result = np.array(scipy.signal.correlate2d(x, x, mode='same', boundary='fill', fillvalue=0))
    return result

def freq_projection(node, x, limit):
    """
    Project frequencies and phases onto one axis
    """
    freq_phases =[]
    limit -= 1
    if(limit > 0):
        height = node.phase
        while(height <0):
            height+=360
        # print(height)
        x1 = x + (1/node.freq)
        freq_phases.append((x1, height))
        for child_node in node.children1:
            freq_phases.extend(freq_projection(child_node, x1, limit))
    return freq_phases

def normalise_freqs(freq_phases):
    """
    Project frequencies and phases onto one axis
    """
    norm_freq_phases=np.empty((len(freq_phases),2))
    denominator_number = 1
    if(len(freq_phases)>1):
        for i in range(0,len(freq_phases)):
            norm_freq_phases[i][0]=freq_phases[i][0]/freq_phases[denominator_number][0]
            norm_freq_phases[i][1] = freq_phases[i][1]
    return norm_freq_phases


def plot_freq_phases(canvas,text1,x_offset,freq_phases ,colour ,transparency=1.0 ,width=2.0, height=60, screen=None):
    global min2,max2
    global max_phase_history
    global iteration_count
    global min1, max1
    global polarX ,polarY
    iteration_count+=1
    max_cols=np.max(freq_phases, axis = 0)
    min_cols = np.min(freq_phases, axis=0)
    min1 = min_cols[0]
    max1 = max_cols[0]
    min2 = min(min1,min2)
    max2 = max(max1,max2)
    max_phases = np.full((700), 80.00)
    max_phases2 = np.full((700), 0.00)
    if(max1==min1):
        max1 =min1 +1
    if (len(freq_phases) <2):
        print("No image data")
        return

    for [freq ,phase] in freq_phases:
        x1 =(freq -min1 ) /(max1 -min1 ) *600
        if(x1 <1):
            phase =360 # None moving line at origin corresponding to bindu.
        max_phases=plot_gaussian(x_offset +x1, height+40, phase, [
            colour[0 ] /256, colour[1 ] /256, colour[2 ] /256], 0.3, 2,max_phases,x_offset,1,screen)
        if(x1>1): #Ignore first frequency which is the observation point
            max_phases2 = calc_gaussian(x1, phase,  max_phases2)

    plot_max(x_offset, height + 40, phase, [
        0 / 256, 1, 0], transparency, width, max_phases, x_offset, 1, screen)
    text1.drawText(canvas, 470, 5,
                    "Normalised Resonance Frequency", 24)
    text1.drawTextRotate(canvas, 255, 200,
                          "Phase", 24, [1, 1, 1, 1], 90)
    mult=280
    offset2=72
    for i in range(0,405,45):
        text_angle=str(i)
        text1.drawText(canvas, 260, offset2 + mult/360*i, text_angle, 18)

    fullscale= max1-min1
    scale_increment=600/fullscale

    write_csv(max_phases2,min2,max2)

    lock.acquire()
    max_phase_history.extend([max_phases2])
    if(len(max_phase_history)>20):
        max_phase_history.pop(0) #remove last element
    lock.release()

    try:
        image = cv2.imread('mygraph1.png')
        cv2.imshow('3D GML', image)
    except:
        print("Can not load plots")


    pause_print=10
    for i in range(0,660):
        freq_ratio = i / 600 * (max1-min1)
        diff_ratio=abs((freq_ratio*4)-round(freq_ratio * 4))
        if(diff_ratio<0.03 and pause_print>5):
            pause_print=0
            text_freq = "{:.2f}".format(round(freq_ratio*4)/4)
            text1.drawTextRotate(canvas, x_offset+i, 40, text_freq, 18,[1,1,1,1],90)
        else:
            pause_print += 1

csv_handle=None
freq_writer=None

csv_summary_written=False

def formated_datetime():
    now = datetime.now(tzlocal.get_localzone())
    datetimestr = datetime.now().strftime("%m/%d/%Y,%H:%M:%S")+str(now.microsecond).zfill(6)+","+now.tzname()
    return datetimestr

def write_csv(max_phases,min1,max1):
    global csv_handle
    global freq_writer
    global csv_summary_written

    datetimestr = formated_datetime()

    try:
        if(csv_handle is None):
            filename = "freq_data/freq_data_"+time.strftime("%Y-%m-%d_%H-%M-%S")+".csv"
            csv_handle=open(filename, 'w', newline='')
            csv_handle.write("Date,Time,TimeZone,Min(Normalised),Max(Normalised), Phases--->")
            csv_handle.write('\n')
        csv_handle.write(datetimestr+',')
        csv_handle.write("1.0," + str(round(max1, 4)) + ",")
        for phase in max_phases:
            csv_handle.write(str(round(phase,6)) + ',')
        csv_handle.write('\n')
    except csv.Error as e:
        sys.exit('file {}, line {}: {}'.format(filename, freq_writer.line_num, e))
    if(csv_summary_written==False):
        write_csv_summary(max_phases, min1, max1)
        csv_summary_written = True



def write_csv_summary(max_phases, min1, max1):
    global freq_writer
    global csv_handle2
    datetimestr = formated_datetime()
    try:
        if(csv_handle2 is None):
            filename = "freq_data/freq_data_summary_"+time.strftime("%Y-%m-%d_%H-%M-%S")+".csv"
            csv_handle2=open(filename, 'w', newline='')
            csv_handle2.write("Date,Time,TimeZone\n")
            csv_handle2.write(datetimestr + '\n')

        bands=  ['Hertz','kiloHertz','MegaHertz','GigaHertz','TeraHertz','PetaHertz']
        units = ['Hz'    ,      'kHz'  ,         'MHz'   ,    'GHz' , 'THz'  , 'Phz']
        multiplier=[1,2,3,4,5,6]

        csv_handle2.write("Derivation of frequencies from scale free analysis---->,,,,,,Phase\n")
        for i in range(0, len(bands)):
            csv_handle2.write(bands[i]+",")
        csv_handle2.write("Angle\n")
        for i in range(0, len(bands)):
            csv_handle2.write(str(multiplier[i])+",")
        csv_handle2.write("\n")
        for i in range(0, len(bands)):
            csv_handle2.write(units[i]+",")
        csv_handle2.write("°\n")

        len_freq = len(max_phases)
        freq_index=0
        for phase in max_phases:
            for i in range(0,len(bands)):
                csv_handle2.write(str(round(freq_index*max1/len_freq*multiplier[i], 3))+',')
            csv_handle2.write(str(round(phase, 4)) + ',')
            freq_index+=1
            csv_handle2.write('\n')
        csv_handle2.close()
    except csv.Error as e:
        sys.exit('file {}, line {}: {}'.format(filename, freq_writer.line_num, e))

def draw_3d_plot():
    global fig1,ax1,ax2,ax3,plt,max_phase_history
    global min1,max1
    if (fig1 is None):
        file_path = "image1.png"
        if os.path.isfile(file_path):
            os.remove(file_path)
        plt.style.use('dark_background')
        plt.close('all')
        fig1 = plt.figure(1)
        # fig1.set_size_inches(7,10.2) # Set the figure size to 7 inches wide and 10.2 inches tall
    plt.figure(1).clear()
    ax1 = fig1.add_subplot(311, projection='3d')
    ax2 = fig1.add_subplot(312)
    ax3 = fig1.add_subplot(313)

    fig1.patch.set_facecolor('black')
    fig1.patch.set_alpha(1.0)
    plt.style.use('dark_background')
    x = np.linspace(min1, max1, 700)

    lock.acquire()
    hist_len = len(max_phase_history)

    shorter_hist_len=min(hist_len,10)
    y = np.linspace(0, shorter_hist_len, shorter_hist_len)
    X, Y = np.meshgrid(x, y)

    max_phases2_np = np.flip(np.array(max_phase_history), 0)
    lock.release()

    if(np.shape(max_phases2_np)[0]==0):
        print("Not plotting")
        return
    Zr=np.resize(max_phases2_np,(shorter_hist_len,np.shape(max_phases2_np)[1]))

    ax1.plot_surface(X, Y, Zr, rstride=1, cstride=1,
                 cmap='inferno', edgecolor='none')
    ax1.set_xlabel('Normalised Frequency')
    ax1.set_ylabel('Time')
    ax1.set_zlabel('Phase');
    ax1.set_title("Spatio-Temporal Dynamics of Scale-Free Resonance Frequencies")

    y = np.linspace(0, hist_len, hist_len)
    X, Y = np.meshgrid(x, y)
    Z = max_phases2_np
    CS = ax2.contour(X, Y, Z, 6)
    ax2.clabel(CS, fontsize=9, inline=True)
    ax2.set_xlabel('Normalised Frequency')
    ax2.set_ylabel('Time');
    ax2.set_title("Contour Projection of Spatio-Temporal Dynamics")
    # plt.pyplot.show(ioff)

    #Auto Correlation
    all_quadrants=False

    cZ=np.zeros([np.shape(Z)[0],np.shape(Z)[1]])
    if(all_quadrants==True):
        cZ=autocorr2d(Z)
        cx = np.linspace(-max1, max1, 700)
        cy = np.linspace(-hist_len, hist_len, hist_len)
    else:
        cZ = autocorr2d_one_quadrant(Z)
        cx = np.linspace(min1, max1, 700)
        cy = np.linspace(0, hist_len, hist_len)

    cX, cY = np.meshgrid(cx, cy)

    levels = np.linspace(0, 360, 360)
    CS2 = ax3.contourf(cX, cY, cZ,360)
    CS2 = ax3.contour(cX, cY, cZ, 50,colors=['#808080', '#A0A0A0', '#C0C0C0'], extend='both')
    ax3.clabel(CS, fontsize=9, inline=True)
    ax3.set_xlabel('Frequency Shift')
    ax3.set_ylabel('Time Shift');
    ax3.set_title("Phase Auto-Correlation of Invariants")

    plt.subplots_adjust(left=0.1,
                        bottom=0.1,
                        right=0.9,
                        top=0.9,
                        wspace=0.4,
                        hspace=0.4)

    fig1.canvas.draw()
    fig1.canvas.flush_events()
    plt.savefig("mygraph1.png",dpi=100)