import math
import trig_tables as trig
from kivy.graphics import *
from kivy.graphics import Line, Color
from kivy.graphics.texture import Texture
from scipy.stats import norm

import numpy as np

screen = None
screen_width = 10
screen_height = 10
BACKGROUND = [100, 100, 100, 100]


def blit_functions_init(window1):
    """
    Set up the global variable pointing to the Pygame screen
    """
    global screen
    global screen_width, screen_height
    window = window1
    screen_width, screen_height = window.size


def screen_get_screen_size():
    """
    Return screen size
    """
    global screen_width, screen_height
    return [screen_width, screen_height]


def screen_get_mid_position():
    """
    Return screen midpoint
    """
    global screen_width, screen_height
    return [screen_width/2, screen_height/2]


def screen_clear(canvas):
    canvas.clear()
    #screen.fill([0,0,0])


def get_pixel_colors(texture, dims):
    """
    Return an array of [rgba] for colours of the given texture
    """
    return None

    pos = (0, 0)
    #print("Image size",dims)
    pixel = texture.get_region(pos[0], pos[1], dims[0], dims[1])
    bp = pixel.pixels
    data = np.frombuffer(bp, dtype=np.uint8).reshape(dims[0], dims[1]*4)
    #print("TextureRegion.pixels = \n", data)
    return data


def get_pixel_color(colour_array, image_dims, pos):
    """
    Return the colour at a point in an array representing a photo
    """
    h = image_dims[1]
    w = image_dims[0]
    index1 = int((pos[0]))
    index2 = int((pos[1])*4)

    if(index1 < 0 or index2 < 0 or index1 > colour_array.shape[0] or index2 > colour_array.shape[1]):
        print("Point outside of image")
        return BACKGROUND

    col = (colour_array[index1, index2+0], colour_array[index1, index2+1],
           colour_array[index1, index2+2], colour_array[index1, index2+3])
    #print("Col=",col)
    return col


def grab_circular_photo_blit(im, colour_array, image_dims, image_scale, texture, x, y, w, h, transparent_colour, scale):
    """
    Grab an area from a photo
    """
    #print(colour_array.shape,image_dims)
    if(w < 10):
        w = 10
    if(h < 10):
        h = 10

    u1 = 2
    v1 = 2
    w1 = 2
    h1 = 2
    loop_count = 0
    while True:
        loop_count += 1
        u1 = (x-w*6)/(image_dims[0]/image_scale)
        v1 = (y-h*6)/(image_dims[1]/image_scale)
        w1 = w/(image_dims[0]/image_scale)*12
        h1 = h/(image_dims[1]/image_scale)*12
        if((u1+w1) < 1 and (v1+h1) < 1 and u1 > 0 and v1 > 0):
            break
        if(loop_count > 10):
            if(loop_count > 20):
                break
            w = w*0.5
            h = h*0.5
        else:
            w = w*0.95
            h = h*0.95

    #print("!!!!    ",int(x),int(y),u1,v1,w1,h1)
    texc = u1, v1, u1 + w1, v1, u1 + w1, v1 + h1, u1, v1 + h1

    w = w*6
    h = h*6

    with canvas:
        fbo = Fbo(size=(w/w1, h/h1))
        fbo.bind()
        fbo.clear_buffer()
        fbo.release()
        with fbo:
            Color(1, 1, 1, 1)
            Rectangle(pos=(0, 0), size=(
                image_dims[0]/6, image_dims[1]/6), texture=texture, tex_coords=texc)

    if(x < 0):
        x = 0
    if(y < 0):
        y = 0
    try:
        s_colour = im.read_pixel(x*image_scale, image_dims[1]-(y*image_scale))
    except:
        s_colour = [0, 0, 0]
    single_colour = [s_colour[0]*255, s_colour[1]*255, s_colour[2]*255, 255]
    return [w, h, fbo, single_colour]


canvas = None
fbo = None


def blit_functions_canvas(canvas1, fbo1):
    global canvas, fbo
    canvas = canvas1
    fbo = fbo1


def create_spiral_blit(pos, r, line_width, colour, transparent_colour, transparency, gears, phase, spiral_rate, spiral_mode, extra_angle):
    """
    Create blit with spiral
    """
    global canvas
    if(r < 1):
        r = 1
    size = (r*2, r*2)
    with canvas:
        colour = [colour[0]/256, colour[1]/256, colour[2]/256, 0.9]
        Color(colour)
        if(line_width == 0):
            r_width = r/2
            Line(circle=(pos[0], pos[1], r_width), width=r_width)
        else:
            Line(circle=(pos[0], pos[1], r), width=1.5)

    oversize = 1.4
    r_over = r*oversize
    with canvas:
        fbo = Fbo(size=(2*r_over, 2*r_over))
        Rectangle(pos=(pos[0]-r_over, pos[1]-r_over),
                  size=(2*r_over, 2*r_over), texture=fbo.texture)
    with fbo:
        ClearColor(0, 0, 0, 0.5)
        if(line_width == 0):
            r_width = r/2
            Color(colour[0], colour[1], colour[2], 1.0)
            Line(circle=(r_over, r_over, r_width), width=r_width)
            Color(0, 0, 0, 0)

        else:
            Color(colour[0], colour[1], colour[2], 1.0)
            for j in range(0, 722):
                k = j/2
                ph = k*spiral_rate
                if(spiral_mode == 1):
                    r1 = abs(k/180-1)*r
                elif(spiral_mode == 2):
                    r1 = (k/180-1)*r
                    if(k >= 180):
                        ph = -ph
                elif(spiral_mode == 3):
                    if(k >= 180):
                        k2 = (360-k)*2
                    else:
                        k2 = k*2
                    r1 = (k2/180-1)*r
                    if(k2 >= 180):
                        ph = -ph
                else:
                    r1 = k/360*r
                if(extra_angle != 0):
                    if(r1 > 0):
                        ph = ph+extra_angle
                x1 = r1*trig.fast_cos(ph/180*math.pi) + r_over
                y1 = r1*trig.fast_sin(ph/180*math.pi) + r_over
                if(k == 0):
                    x2 = x1
                    y2 = y1
                Line(points=[x1, y1, x2, y2], width=2.0)
                x2 = x1
                y2 = y1
            Color(0, 0, 0, 0)
    fbo.draw()
    return [r_over, r_over, fbo]


def create_circular_blit(pos, r, line_width, colour, transparent_colour, transparency, gears, phase):
    
    # Create blit with circle
    
    global canvas
    if(r < 1):
        r = 1
    if(gears == True):
        r = r*1.3
    size = (r*2, r*2)
    with canvas:
        colour = [colour[0]/256, colour[1]/256, colour[2]/256, 0.9]
        Color(colour)
        if(line_width == 0):
            r_width = r/2
            Line(circle=(pos[0], pos[1], r_width), width=r_width)
        else:
            Line(circle=(pos[0], pos[1], r), width=1.5)

    if(gears == False):
        oversize = 1.4
    else:
        oversize = 1.0
    r_over = r*oversize
    with canvas:
        fbo = Fbo(size=(2*r_over, 2*r_over))
        #Color(1, 1, 0.8)
        Rectangle(pos=(pos[0]-r_over, pos[1]-r_over),
                  size=(2*r_over, 2*r_over), texture=fbo.texture)
    with fbo:
        ClearColor(0, 0, 0, 0.5)
        if(line_width == 0):
            r_width = r/2
            if(gears == False):
                Color(colour[0], colour[1], colour[2], 1.0)
                Line(circle=(r_over, r_over, r_width), width=r_width)
                Color(0, 0, 0, 0)
            else:
                Color(colour[0], colour[1], colour[2], 1.0)
                Line(circle=(r, r, r), width=line_width)
                spokes = int((r/20)+3)
                for k in range(spokes+3):
                    x1 = 0.48*r*trig.fast_cos(2*math.pi*k/spokes) + r
                    y1 = 0.48*r*trig.fast_sin(2*math.pi*k/spokes) + r

                    if (k > 0):
                        if(spokes > 6):
                            x2 = 0.98*r*trig.fast_cos(2*math.pi*k/spokes) + r
                            y2 = 0.98*r*trig.fast_sin(2*math.pi*k/spokes) + r
                            #Color(colour[0],colour[1],colour[2],1.0)
                            Line(points=[r, r, x2, y2], width=10)
                            #Color(colour[0],colour[1],colour[2],1.0)
                            Line(circle=(x1, y1, int(r/2)), width=4)
                Color(0, 0, 0, 0)

        else:
            Color(colour[0], colour[1], colour[2], 1.0)
            Line(circle=(r_over, r_over, r), width=2.0)
            Color(0, 0, 0, 0)

    fbo.draw()
    if(gears == True):
        plot_rotated_centre_blit([r, r, fbo], (pos[0], pos[1]), phase)
    return [r_over, r_over, fbo]


def grab_circular_colour(image1, r):
    
    # Grab colour from the middle of an area
    
    global canvas
    if(image1 == None):
        print("grab_circular empty")
        return [80, 80, 80]
    if(r < 1):
        r = 1
    
    with canvas:
        colour = get_pixel_color(image1.texture, [int(r/4), int(r/4)])
    return colour[0] * 255, colour[1] * 255, colour[2] * 255


def create_star_blit(pos, r, thickness, colour, transparent_colour, transparency):

    # Create blit with star, create_star_blit(pos,100,5,[255,0,0],[0,0,0],1.0)
    global canvas
    oversize = 1.4
    r_over = r*oversize
    with canvas:
        fbo = Fbo(size=(2*r_over, 2*r_over))
        Rectangle(pos=(pos[0]-r_over, pos[1]-r_over),
                  size=(2*r_over, 2*r_over), texture=fbo.texture)
    with fbo:
        ClearColor(0, 0, 0, 0.5)
        Color(colour[0], colour[1], colour[2], transparency)
        if(r < 1):
            r = 1
        size = (r*2, r*2)
        for k in range(6):
            x1 = r*trig.fast_cos(4*math.pi*k/5 + 0.5*math.pi) + r
            y1 = r*trig.fast_sin(4*math.pi*k/5 + 0.5*math.pi) + r
            if(k > 0):
                Line(points=[x1, y1, x2, y2], width=thickness)
            x2 = x1
            y2 = y1

    fbo.draw()
    return [r, r, fbo]


def plot_centre_blit(part, pos):
    
    # Plot an area after rotating preserving centre of the image
    
    global canvas
    with canvas:
        r1 = part[0]
        r2 = part[1]
        Rectangle(pos=(pos[0]-r1, pos[1]-r2),
                  size=(2*r1, 2*r2), texture=part[2].texture)
    return [r1, r2, part]


def plot_rotated_blit(part, pos, angle, ellipse_mask=False, transparency=1.0):
    """
    Plot an area after rotating
    """
    global canvas
    with canvas:
        r1 = part[0]
        r2 = part[1]
        PushMatrix()
        Rotate(angle=angle, origin=(pos[0], pos[1]))

        if(ellipse_mask == True):
            StencilPush()
            Ellipse(pos=(pos[0], pos[1]), size=(2*r1, 2*r2))
            StencilUse()
        Color(1, 1, 1, transparency)
        Rectangle(pos=(pos[0], pos[1]), size=(
            2*r1, 2*r2), texture=part[2].texture)
        if(ellipse_mask == True):
            StencilPop()
        PopMatrix()
    return [r1, r2, part]


def plot_rotated_centre_blit(part, pos, angle, ellipse_mask=False, transpareny=1.0):
    """
    Plot an area after rotating preserving centre of the image
    """
    global canvas
    with canvas:
        r1 = part[0]
        r2 = part[1]
        PushMatrix()
        Rotate(angle=angle, origin=(pos[0], pos[1]))

        if(ellipse_mask == True):
            StencilPush()
            Ellipse(pos=(pos[0]-r1, pos[1]-r2), size=(2*r1, 2*r2))
            StencilUse()
        Color(1, 1, 1, transpareny)
        Rectangle(pos=(pos[0]-r1, pos[1]-r2),
                  size=(2*r1, 2*r2), texture=part[2].texture)
        if(ellipse_mask == True):
            StencilPop()
        PopMatrix()
    return [r1, r2, part]


def plot_lines(line_points, colour, transparency, width, screen=None):
    """
    Plot a line
    """
    if(screen==None):
        global canvas
    else:
        canvas=screen
    with canvas:
        #r1=part[0]
        #r2=part[1]
        ClearColor(0, 0, 0, 0.5)
        Color(colour[0], colour[1], colour[2], transparency)
        Line(points=line_points, width=width)
    #return [r1,r2,part]


sigma=10
sigma_constant=sigma*math.sqrt(2*math.pi)

def plot_gaussian(x_offset, y_offset, height, colour, transparency, width,max_phases, raw_x_offset=0, xscale=600, screen=None):
    global sigma_constant
    xy_plot = []
    x_axis_length=1000
    y_axis_length=350
    if (height == 360):
        x_axis = np.arange(0, 50, 1)  # +x_offset
    else:
        x_axis = np.arange(-50, 50, 1)  # +x_offset
    y_axis = norm.pdf(x_axis, 0, sigma)*sigma_constant*height+y_offset
    x_axis2 = x_axis+x_offset
    #xy_plot.extend((0, y_offset))
    for i in range(len(x_axis)):
        xy_plot.extend((x_axis2[i], y_axis[i]))
        x_test_pos=int(x_axis2[i] - raw_x_offset)
        if(y_axis[i]>max_phases[x_test_pos]):
            max_phases[x_test_pos]=y_axis[i]
    plot_lines(xy_plot, colour, transparency, width, screen)
    if(height==360):
        xy_plot = []
        xy_plot.extend((x_axis_length, y_offset))
        xy_plot.extend((x_axis_length-5, y_offset-5))
        xy_plot.extend((x_axis_length, y_offset))
        xy_plot.extend((x_axis_length-5, y_offset+5))
        xy_plot.extend((x_axis_length, y_offset))
        xy_plot.extend((x_offset, y_offset))
        xy_plot.extend((x_offset, y_offset+y_axis_length))
        xy_plot.extend((x_offset-5, y_offset + y_axis_length -5))
        xy_plot.extend((x_offset, y_offset + y_axis_length))
        xy_plot.extend((x_offset + 5, y_offset + y_axis_length - 5))
        plot_lines(xy_plot, colour, 1.0, width, screen)
    #print(xy_plot)
    return max_phases


def calc_gaussian(freq, phase,max_phases):
    global sigma_constant
    if (phase == 360):
        x_axis = np.arange(0, 50, 1)
    else:
        x_axis = np.arange(-50, 50, 1)
    y_axis = norm.pdf(x_axis, 0, 10)*phase * sigma_constant
    x_axis2 = x_axis+freq
    #xy_plot.extend((0, y_offset))
    for i in range(len(x_axis)):
        x_test_pos=int(x_axis2[i])
        if(y_axis[i]>max_phases[x_test_pos]):
            max_phases[x_test_pos]=y_axis[i]
    return max_phases

def plot_max(x_offset, y_offset, height, colour, transparency, width,max_phases, raw_x_offset=0, xscale=600, screen=None):
    xy_plot = []
    x_count=x_offset
    for i in max_phases:
        xy_plot.extend((x_count, i))
        x_count+=1

    plot_lines(xy_plot, colour, transparency, width, screen)
    return max_phases