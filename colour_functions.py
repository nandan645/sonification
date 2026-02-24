from random import randint

BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)

def subtractColours (colour1,colour2,wrap):
    """
    Generate a colour as a difference of two supplied colours
    """
    new_colour=[0,0,0]
    for i in range(0,2):
        new_colour[i]=colour1[i]+colour2[i]
        if (new_colour[i]>255):
            new_colour[i]=wrap
        if(new_colour[i]<0):
            new_colour[i]=255
    return new_colour

def saturateColour(colour1,sat):
    """
    Generate a colour which is more intense
    """
    new_colour=[0,0,0,255]
    for ind in range(0,3):
        if(new_colour[ind]>127):
            new_colour[ind]=int((colour1[ind]+10)*sat)
        else:
            new_colour[ind]=int((colour1[ind]-4)/sat)
        if (new_colour[ind]>255):
            new_colour[ind]=255
        elif (new_colour[ind]<40):
            new_colour[ind]=40
    return new_colour

def randColour(min,max):
    """
    Return a random colour
    """
    return [randint(min[0],max[0]),randint(min[1],max[1]),randint(min[2],max[2])]
