import math
from blit_functions import *
import trig_tables as trig
from colour_functions import *


def GML_init():
    """
    Allow global initialisation of the PyGame top level screen
    """
    trig.create_tables()
    GMLBaseClass.screen_width, GMLBaseClass.screen_height = screen_get_screen_size()


def GML_resize():
    GMLBaseClass.screen_width, GMLBaseClass.screen_height = screen_get_screen_size()


class GMLBaseClass(object):
    """
    Base class for all GML trees of any dimension
    """
    osc_count = 0
    run_count = 0
    reverse = False
    pause = False
    draw_mode = 0
    screen_width = 0
    screen_height = 0
    oscillator_speed = 1

    def set_reverse(self, rev):
        """
        Change the phase direction for rotating singularities
        """
        GMLBaseClass.reverse = rev

    def set_pause(self, pau):
        """
        Pause/unpause the singularity phase rotation
        """
        GMLBaseClass.pause = pau

    def set_draw_mode(self, draw_m):
        """
        Set drawing mode
        """
        GMLBaseClass.draw_mode = draw_m
        #print(draw_m)

    def set_oscillator_speed(self, new_speed):
        """
        Set overall oscillator speeds
        """
        GMLBaseClass.oscillator_speed = new_speed

    def oscillators(self):
        """
        Return a count of the number of oscillators
        """
        return GMLBaseClass.osc_count

    def reset_run_counter(self):
        """
        Reset a count of the running oscillators
        """
        GMLBaseClass.run_count = 0

    def reset_osc_count(self):
        """
        Reset the counter containing total number of
        oscillators in the tree
        """
        GMLBaseClass.osc_count = 0

    def run_counter(self):
        """
        Returns the current number of oscillators running
        """
        return GMLBaseClass.run_count


class GML_2D(GMLBaseClass):  # , NodeMixin):  # Add Node feature
    """
    The 2D instance of a GML nested tree of oscillators
    """

    def __init__(self, name, diameter, colour, freq, phase, area=None, parent=None, child=None):
        """
        Initialuse a GML_2D object which could be a parent or child
        """
        super(GML_2D, self).__init__()
        self.count = 0
        self.name = name
        self.diameter = diameter
        self.colour = colour
        if (freq == 0):
            self.bindu = True
            freq = 0.5
        else:
            self.bindu = False
        self.freq = (100)/freq+0.1
        self.orbit_radius = abs(freq)
        self.phase = phase
        self.start_phase = phase
        self.parent = parent
        self.mypos = [GMLBaseClass.screen_width
                      / 2, GMLBaseClass.screen_height/2]
        self.mypos2 = [GMLBaseClass.screen_width
                       / 2, GMLBaseClass.screen_height/2]
        self.cursor_pos = [GMLBaseClass.screen_width
                           / 2, GMLBaseClass.screen_height/2]
        self.cursor_phase = phase
        self.visited = False
        self.children1 = []
        self.image_cache = [None, None, None, None, None, None, None, None]
        # if child:  # set children only if given
        #     self.children = children
        if (parent != None):
            parent.add_child(self)
        GMLBaseClass.osc_count += 1
        self.relay_flag = False
        self.relay_hysteresis = 0
        self.area = area
        self.is_spiral = False
        self.spiral_rate = 1
        self.spiral_mode = 1
        self.spiral_rotates = 0
        self.is_pendulum = False
        self.is_angle = False
        self.angle_offset = 0
        self.identifier = -1
        self.probability = 1

    def set_freq(self, freq):
        self.freq = (100)/freq+0.1
        self.orbit_radius = abs(freq)

    def set_identifier(self, id):
        """
        Set an identifier number for tracking GML circles
        against external features
        """
        self.identifier = id

    def set_probability(self, prob):
        #print("Singularity probability:",prob)
        if(prob > 1.0):
            self.probability = 1.0
        else:
            self.probability = prob

    def probability_volume(self):
        prob_vol = (50 ** (self.probability))/50
        #print("Volume based on probability:",prob_vol)
        return prob_vol

    def read_identifiers(self, limit):
        """
        Returns a list of identifiers, frequencies and
        cursor phases
        """
        limit -= 1
        list1 = [[self.identifier, self.freq, self.cursor_phase]]
        if(limit > 0):
            for child_node in self.children1:
                if (child_node != None):
                    list1.extend(child_node.read_identifiers(limit))
        #print(list1)
        return list1

    def update_area(self, new_area):
        """
        Update area or photo associated with this singularity
        """
        #self.image_cache=[None,None,None,None,None,None,None,None]
        self.area = new_area

    def update_colour(self, new_area_colour):
        """
        Update colour associated with this singularity
        """
        #self.image_cache=[None,None,None,None,None,None,None,None]
        self.colour = new_area_colour

    def add_child(self, node):
        """
        Add a child to the current tree node.
        """
        self.children1.append(node)

    def remove_child(self, node):
        """
        Remove a child from the current tree node.
        """
        self.children1.remove(node)

    def get_cartesian_pos(self):
        """
        Return cartesian position of this singularity
        """
        return [self.mypos[0], self.mypos[1]]

    def return_orbit_radius(self):
        """
        Return orbit radius (period)
        """
        return self.orbit_radius

    def clear_visited(self):
        """
        Clear a flag showing this node has been visited
        """
        self.visited = False

    def calc_mypos(self):
        """
        Sum the positions dependent on phases to calculate
        the position of this singularity
        """
        #radians=self.phase/180*math.pi
        #print("Calc:"+str(self.phase))
        if(self.is_spiral == False):
            self.pos = [self.orbit_radius*trig.fast_cos_deg(
                self.phase), self.orbit_radius*trig.fast_sin_deg(self.phase)]
        else:
            spiral_angle = self.phase*self.spiral_rate
            if(self.spiral_mode == 1):
                spiral_amount = abs(self.phase/180-1)
            elif(self.spiral_mode == 2):
                spiral_amount = self.phase/180-1
                if(self.phase > 180):
                    spiral_angle = -spiral_angle
            elif(self.spiral_mode == 3):
                if(self.phase >= 180):
                    ph2 = (360-self.phase)*2
                else:
                    ph2 = self.phase*2
                spiral_amount = ph2/180-1
                if(ph2 > 180):
                    spiral_angle = -spiral_angle
            else:
                spiral_amount = self.phase/360
            if(self.is_pendulum == True):
                spiral_amount = 1
            spiral_angle += self.phase*self.spiral_rotates
            if(self.is_angle == True):
                if (spiral_amount > 0):
                    spiral_angle += self.angle_offset
            self.pos = [self.orbit_radius*spiral_amount*trig.fast_cos_deg(
                spiral_angle), self.orbit_radius*spiral_amount*trig.fast_sin_deg(spiral_angle)]
        if(self.parent == None):
            self.mypos = [GMLBaseClass.screen_width
                          / 2, GMLBaseClass.screen_height/2]
        else:
            self.mypos = self.parent.mypos
        self.mypos = [self.mypos[0]+self.pos[0], self.mypos[1]+self.pos[1]]

    def nearest(self, test_pos, max_distance, limit):
        """
        Recursive function to find the singularity nearest to a
        given cartesian position
        """
        limit -= 1
        self.calc_mypos()
        if(self.parent == None):
            best_node = self
        else:
            best_node = self.parent
        distance = (math.sqrt(
            ((self.mypos[0] - test_pos[0])**2) + ((self.mypos[1] - test_pos[1])**2)))

        if(distance < max_distance):
            best_node = self
            max_distance = distance

        if(limit > 0):
            for child_node in self.children1:
                if (child_node != None):
                    [new_node, max] = child_node.nearest(
                        test_pos, max_distance, limit)
                    if(max < max_distance):
                        best_node = new_node
                        max_distance = max
        return [best_node, max_distance]

    def angleTo(self, test_pos):
        """
        Returns angle to a test position from this singularity
        """
        self.calc_mypos()
        return trig.fast_atan2(test_pos[1]-self.mypos[1], test_pos[0]-self.mypos[0]) / math.pi*180

    def angleToParent(self, test_pos):
        """
        Returns angle to a test position from the parent if this is
        not the root singularity
        """
        if(self.parent == None):
            return self.angleTo(test_pos)
        else:
            return self.parent.angleTo(test_pos)

    def distanceTo(self, test_pos):
        """
        Returns distance to a test position from this singularity
        """
        self.calc_mypos()
        return((((self.mypos[0] - test_pos[0])**2) + ((self.mypos[1] - test_pos[1])**2))**0.5)

    def distanceToParent(self, test_pos):
        """
        Returns distance to the parent singularity if this is
        not the root node
        """
        if(self.parent == None):
            return self.distanceTo(test_pos)
        else:
            return self.parent.distanceTo(test_pos)

    def frequency_list(self, limit):
        """
        Iterate, building a list of frequencies
        """
        res = []
        limit -= 1
        if(limit > 0):
            for child_node in self.children1:
                if (child_node != None):
                    res = res+child_node.frequency_list(limit)
        res.append(1.0 / self.freq)
        res.sort()
        return res

    def periods_list(self, limit):
        """
        Iterate, building a list of periods (1/f)
        """
        res = []
        limit -= 1
        if(limit > 0):
            for child_node in self.children1:
                if (child_node != None):
                    res = res+child_node.periods_list(limit)
        res.append(self.freq)
        res.sort()
        return res

    def adjacient_ratio_list(self, limit):
        """
        Iterate, building a list of adjacent frequencies
        """
        res = []
        limit -= 1
        if(limit > 0):
            for child_node in self.children1:
                if (child_node != None):
                    res.append((1.0/child_node.freq) / (1.0/self.freq))
                    res = res+child_node.adjacient_ratio_list(limit)
        res.sort()
        return res

    def run1_areas(self, limit):
        """
        Iterate, drawing captured photo areas
        """
        if(self.area != None and GMLBaseClass.draw_mode != 7 and GMLBaseClass.draw_mode != 2):
            plot_rotated_centre_blit(
                self.area, self.mypos, self.start_phase-self.phase, True, 0.8)
        limit -= 1
        if(limit > 0):
            for child_node in self.children1:
                if (child_node != None):
                    child_node.run1_areas(limit)

    def run1(self, limit, inverse_gml=False):
        """
        Perform one iteration of the GML tree, calculating
        new phase positions for all singularity points in the GML tree
        """
        GMLBaseClass.run_count += 1
        if(GMLBaseClass.pause != True):
            if(GMLBaseClass.reverse == True):
                self.phase -= self.freq * GMLBaseClass.oscillator_speed
            else:
                self.phase += self.freq * GMLBaseClass.oscillator_speed
            if(self.phase > 360):
                self.phase -= 360

        self.calc_mypos()
        if(self.parent == None):
            self.mypos2 = [GMLBaseClass.screen_width
                           / 2, GMLBaseClass.screen_height/2]
            #print("Mypos",self.mypos)
        else:
            self.mypos2 = self.parent.mypos

        #print("Mypos",self.mypos)
            #Draw the orbit circle
        if(GMLBaseClass.draw_mode >= 2 and GMLBaseClass.draw_mode < 7):
            if(self.image_cache[0] != None):
                if(self.is_spiral and self.spiral_rotates != 0):
                    plot_rotated_centre_blit(
                        self.image_cache[0], self.mypos2, self.phase*self.spiral_rotates)
                else:
                    plot_centre_blit(self.image_cache[0], self.mypos2)
            else:
                if(self.is_spiral):
                    self.image_cache[0] = create_spiral_blit(self.mypos2, self.orbit_radius, 2, self.colour, [
                                                             0, 0, 0], 200, False, self.phase, self.spiral_rate, self.spiral_mode, self.angle_offset)
                else:
                    self.image_cache[0] = create_circular_blit(
                        self.mypos2, self.orbit_radius, 2, self.colour, [0, 0, 0], 200, False, self.phase)
        elif(GMLBaseClass.draw_mode >= 7):
            max_r = 0
            for child_node in self.children1:
                if (child_node != None):
                    if(child_node.orbit_radius > max_r):
                        max_r = child_node.orbit_radius  # *0.67
            if(self.image_cache[1] != None):
                plot_rotated_centre_blit(
                    self.image_cache[1], self.mypos, self.phase)
            else:
                self.image_cache[1] = create_circular_blit(
                    self.mypos, self.orbit_radius-max_r, 4, self.colour, [0, 0, 0], 200, True, self.phase)
            #pygame.draw.circle(screen,self.colour, self.mypos , self.orbit_radius, 1)
        newpos = [self.mypos2[0]+self.pos[0], self.mypos2[1]+self.pos[1]]
        #pygame.draw.line(screen,self.colour, self.mypos ,newpos,1)
        self.mypos2 = newpos
        #Draw the singularity
        if(GMLBaseClass.draw_mode >= 3):
            if(self.image_cache[2] != None):
                plot_centre_blit(self.image_cache[2], self.mypos2)
            else:
                self.image_cache[2] = create_circular_blit(
                    self.mypos2, self.diameter, 0, self.colour, [0, 0, 0], 200, False, 0)
            #pygame.draw.circle(screen,self.colour, self.mypos , self.diameter, 0)
        limit -= 1
        if(limit > 0):
            for child_node in self.children1:
                if (child_node != None):
                    child_node.run1(limit)

    def reset_phases(self, limit):
        """
        Reset phases to their starting state and re-compute
        the positions
        """
        self.phase = self.start_phase
        self.calc_mypos()
        limit -= 1
        if(limit > 0):
            for child_node in self.children1:
                if (child_node != None):
                    child_node.reset_phases(limit)

    def reset_child_cursors(self, limit):
        """
        Visit children and reset their cursors to their initial
        phase positions in order to synchronise clocks
        """
        limit -= 1
        if(limit > 0):
            for child_node in self.children1:
                if (child_node != None):
                    child_node.reset_cursor()
                    child_node.reset_child_cursors(limit)

    def set_cursor(self, new_phase):
        """
        Set the cursor to a new phase. Used for tracking.
        """
        #print("Cursor phase set:",self.cursor_phase)
        self.cursor_phase = new_phase

    def reset_cursor(self):
        """
        Set the cursor to the current singularity phase position
        """
        print("Cursor phase reset:", self.phase)
        self.cursor_phase = self.phase

    def advance_cursor(self, dist):
        """
        Advance the cursor the equivalent of a linear time distance
        """
        #print("advancing cursor")
        angle_change = (dist / (self.orbit_radius)) * 180  # *360  #180
        #print("orbit radius=",self.orbit_radius," dist=",angle_change," cursor phase=",self.cursor_phase)
        self.cursor_phase += angle_change
        if(self.cursor_phase < 0):
            self.cursor_phase += 360
        if(self.cursor_phase > 1440):
            self.cursor_phase -= 1440

    def get_ang_diff(self, a1, a2):
        """
        Generic angle differences function
        """
        r = (a2 - a1) % 360.0
        if r >= 180.0:
            r -= 360.0
        return r

    def cursor_overlap_check(self, dist):
        """
        Check if the cursor is overlapping the singularity
        If it is return True plus return an angular measure of overlap
        """
        #diff=abs(self.get_ang_diff(self.phase,self.cursor_phase))
        diff = (self.get_ang_diff(self.phase, self.cursor_phase))
        abs_diff = abs(diff)
        if(abs_diff < dist and diff > 0):
            ret_val = [True, abs_diff, diff]
        else:
            ret_val = [False, 0, 0]
        return ret_val

    def cursor_radius(self):
        """
        Return the orbital radius of this singularity
        """
        return self.orbit_radius

    def calc_cursor_pos(self):
        """
        Calculate the cartesian position of the cursor
        """
        self.calc_mypos()
        #radians=self.cursor_phase/180*math.pi
        if(self.is_spiral == False):
            new_pos = [self.orbit_radius*trig.fast_cos_deg(
                self.cursor_phase), self.orbit_radius*trig.fast_sin_deg(self.cursor_phase)]
        else:
            spiral_angle = self.phase*self.spiral_rate
            if(self.spiral_mode == 1):
                spiral_amount = abs(self.cursor_phase/180-1)
            elif(self.spiral_mode == 2):
                spiral_amount = self.cursor_phase/180-1
                if(self.cursor_phase > 180):
                    spiral_angle = -spiral_angle
            elif(self.spiral_mode == 3):
                if(self.cursor_phase >= 180):
                    ph2 = (360-self.cursor_phase)*2
                else:
                    ph2 = self.cursor_phase*2
                spiral_amount = ph2/180-1
                if(ph2 > 180):
                    spiral_angle = -spiral_angle
            else:
                spiral_amount = self.cursor_phase/360
            spiral_angle += self.cursor_phase*self.spiral_rotates
            if(self.is_pendulum == True):
                spiral_amount = 1
            if(self.is_angle == True):
                if (spiral_amount > 0.5):
                    spiral_angle += self.angle_offset
            new_pos = [self.orbit_radius*spiral_amount*trig.fast_cos_deg(
                spiral_angle), self.orbit_radius*spiral_amount*trig.fast_sin_deg(spiral_angle)]
        if(self.parent == None):
            parent = [GMLBaseClass.screen_width
                      / 2, GMLBaseClass.screen_height/2]
            #best_node=self
        else:
            parent = self.parent.mypos
            #best_node=self.parent
        self.cursor_pos = [parent[0]+new_pos[0], parent[1]+new_pos[1]]

    def return_cursor_pos(self):
        """
        Return the cartesian position of the cursor
        """
        return [self.cursor_pos[0], self.cursor_pos[1]]

    def get_relay_flag(self):
        """
        Return the relay_flag
        """
        return self.relay_flag
        #if (self.relay_hysteresis==0 and self.relay_flag==True):
        #    self.relay_hysteresis=1
        #    return True
        #else:
        #    if(self.relay_hysteresis>0):
        #        self.relay_hysteresis-=1
        #return False

    def set_relay_flag(self, val):
        """
        Set the relay_flag value used for
        tracking microtubule mode
        """
        self.relay_flag = val
        #self.relay_hysteresis=1

    def add_polygon(self, name, sides, offset_angle, diameter, freq, colour, levels=1, freq_factor=1.0, polygon_factor=0, rotation_factor=0, crystal=False, colour_change=False):
        """
        Add an n sided polygon to the current node.
        If levels is provided, a set of nested polygon is added.
        Optional parameters:
        => frequency_factor is a multiplier on the circle size for each nest.
        => polygon_factor is an integer increment or decrement of the number of
        side on each nest.
        => rotation_factor is an integer describing an increment or decrement of
        the number of sides as the shape is rotated.
        """
        node = None
        nodes = []
        angle = offset_angle
        levels -= 1
        rotation_adj = 0
        if(sides <= 0):
            sides = 0
            ang_inc = 0
        else:
            angle_incr = (360/sides)
        for vertex in range(sides):
            node = GML_2D(name+str(levels)+"_"+str(vertex+1),
                          diameter, colour, freq, angle, None, parent=self)
            if(colour_change):
                colour = subtractColours(colour, [-11, -50, -30], 60)
            if(levels > 0):
                if(crystal == True):
                    node.add_polygon(name, sides+polygon_factor+rotation_adj,
                                     offset_angle, diameter, freq*freq_factor, colour, levels)
                else:
                    node.add_polygon(name, sides+polygon_factor+rotation_adj, offset_angle, diameter, freq
                                     * freq_factor, colour, levels, freq_factor, polygon_factor, rotation_factor, crystal)
            angle += angle_incr
            rotation_adj += rotation_factor
            nodes.append(node)
        if(len(nodes) > 0):
            return nodes
        else:
            return self

    def add_line(self, angle1, angle2, diameter, freq, colour):
        """
        Add a line that is two arbitrary singularity points
        on the same circle defined by two angles
        """
        node1 = GML_2D("LineA", diameter, colour,
                       freq, angle1, None, parent=self)
        node2 = GML_2D("LineB", diameter, colour,
                       freq, angle2, None, parent=self)
        return (node1, node2)

    def add_spiral(self, angle1, diameter, freq, colour, spiral_rate, spiral_mode, spiral_rotates):
        """
        Add a spiral
        """
        node1 = GML_2D("Spiral", diameter, colour,
                       freq, angle1, None, parent=self)
        node1.spiral_rate = spiral_rate
        node1.is_spiral = True
        node1.spiral_mode = spiral_mode
        node1.spiral_rotates = spiral_rotates
        node1.is_pendulum = False
        return node1

    def add_linear(self, angle1, diameter, freq, colour, linear_mode, linear_rotates):
        """
        Add a linear object
        """
        node1 = GML_2D("Linear", diameter, colour,
                       freq, angle1, None, parent=self)
        node1.spiral_rate = 0
        node1.is_spiral = True
        node1.spiral_mode = linear_mode
        node1.spiral_rotates = linear_rotates
        node1.is_pendulum = False
        return node1

    def add_pendulum(self, angle1, diameter, freq, colour, linear_mode, linear_rotates):
        """
        Add a pendulum object (A straight)
        """
        node1 = GML_2D("Pendulum", diameter, colour,
                       freq, angle1, None, parent=self)
        node1.spiral_rate = 0
        node1.is_spiral = True
        node1.spiral_mode = linear_mode
        node1.spiral_rotates = linear_rotates
        node1.is_pendulum = True
        return node1

    def add_angle(self, angle1, diameter, freq, colour, linear_mode, linear_rotates, angle_offset):
        """
        Add an angle object
        """
        node1 = GML_2D("Angle", diameter, colour,
                       freq, angle1, None, parent=self)
        node1.spiral_rate = 0
        node1.is_spiral = True
        node1.spiral_mode = linear_mode
        node1.spiral_rotates = linear_rotates
        node1.is_pendulum = False
        node1.is_angle = True
        node1.angle_offset = 180-angle_offset
        return node1

    def add_corner(self, angle1, diameter, freq, colour, linear_mode, linear_rotates):
        """
        Add a corner object
        """
        node1 = GML_2D("Corner", diameter, colour,
                       freq, angle1, None, parent=self)
        node1.spiral_rate = 0
        node1.is_spiral = True
        node1.spiral_mode = linear_mode
        node1.spiral_rotates = linear_rotates
        node1.is_pendulum = False
        node1.is_angle = True
        node1.angle_offset = 90
        return node1

    def add_cross(self, angle1, diameter, freq, colour, linear_mode, linear_rotates):
        pass

    def add_singularity(self, offset_angle, diameter, freq, colour, levels=1, freq_factor=1.0):
        """
        Add singularity points to the current circle
        """
        return self.add_polygon("Singularity", 1, offset_angle, diameter, freq, colour, levels, freq_factor)

    def add_dipole(self, offset_angle, diameter, freq, colour, levels=1, freq_factor=1.0):
        """
        Add a dipole consisting of two singularity points opposite
        each other on the circle forming a diameter
        """
        return self.add_polygon("Dipole", 2, offset_angle, diameter, freq, colour, levels, freq_factor)

    def add_triangle(self, offset_angle, diameter, freq, colour, levels=1, freq_factor=1.0):
        """
        Add an equalateral triangle to the current node
        """
        return self.add_polygon("Triangle", 3, offset_angle, diameter, freq, colour, levels, freq_factor)

    def add_square(self, offset_angle, diameter, freq, colour, levels=1, freq_factor=1.0):
        """
        Add a square to the current node
        """
        return self.add_polygon("Square", 4, offset_angle, diameter, freq, colour, levels, freq_factor)

    def add_pentagon(self, offset_angle, diameter, freq, colour, levels=1, freq_factor=1.0):
        """
        Add a pentagon to the current node
        """
        return self.add_polygon("Pentagon", 5, offset_angle, diameter, freq, colour, levels, freq_factor)

    def add_hexagon(self, offset_angle, diameter, freq, colour, levels=1, freq_factor=1.0):
        """
        Add a hexagon to the current node
        """
        return self.add_polygon("Hexagon", 6, offset_angle, diameter, freq, colour, levels, freq_factor)

    def add_heptagon(self, offset_angle, diameter, freq, colour, levels=1, freq_factor=1.0):
        """
        Add a heptagon to the current node
        """
        return self.add_polygon("Heptagon", 7, offset_angle, diameter, freq, colour, levels, freq_factor)

    def add_polygon_list(self, name, polygon_list, offset_angle, diameter, freq, colour, freq_factor=1.0, random_colour=False):
        """
        Method to create a GML from a list.
        The list defines the nested geometry which for each spur
        terminates when a zero value in the list is reached.
        """
        angle = offset_angle
        list_len = len(polygon_list)
        if(list_len > 0):
            sides = polygon_list.pop(0)
            if(sides <= 0):
                sides = 0
                ang_inc = 0
            else:
                angle_incr = (360/sides)
            for vertex in range(sides):
                if(random_colour == True):
                    colour = randColour([100, 0, 150], [255, 0, 255])
                node = GML_2D(name+str(list_len)+"_"+str(vertex+1),
                              diameter, colour, freq, angle, None, parent=self)
                if(sides > 0):
                    node.add_polygon_list(name, polygon_list, offset_angle, diameter,
                                          freq*freq_factor, colour, freq_factor, random_colour)
                angle += angle_incr
        return self

    def nth_child(self, num=0):
        """
        Returns first child node
        """
        if (self.children1 != None):
            if(num < len(self.children1)):
                return self.children1[num]
            else:
                return self
        else:
            return self

    def print_tree(self, str1=""):
        """
        Print a text tree layout
        """
        str2 = str1+self.name+" " + \
            str(round(self.freq, 3))+" "+str(round(self.phase, 2))
        print(str2)
        if(len(self.children1) > 0):
            count = 0
            last = len(self.children1)-1
            for child_node in self.children1:
                if(count != last):
                    str3 = str1.replace("-", " ").replace("+", " ")+"|--"
                else:
                    str3 = str1.replace("-", " ").replace("+", " ")+"+--"
                child_node.print_tree(str3)
                count += 1
        else:
            print(str1.replace("-", " ").replace("+", " "))
        pass

    def dimensions(self, dim=0):
        """
        Return maximum number of dimendsions used
        """
        max_dim = dim
        for child_node in self.children1:
            dim1 = child_node.dimensions(dim+1)
            if(dim1 > max_dim):
                max_dim = dim1
        return max_dim

    def x_child_projection(self, limit, colour, x):
        """
        Project children onto one axis
        """
        #self.calc_mypos()
        limit -= 1
        if(limit > 0):
            if (len(self.children1) == 0):
                #Reached a child
                if(self.image_cache[3] != None):
                    plot_centre_blit(self.image_cache[3], [x, self.mypos[1]])
                else:
                    self.image_cache[3] = create_circular_blit(
                        [x, self.mypos[1]], self.diameter, 0, colour, [0, 0, 0], 200, False, 0)
            for child_node in self.children1:
                child_node.x_child_projection(limit, colour, x)
        return

    def y_child_projection(self, limit, colour, y):
        """
        Project children onto one axis
        """
        #self.calc_mypos()
        limit -= 1
        if(limit > 0):
            if (len(self.children1) == 0):
                #Reached a child
                if(self.image_cache[4] != None):
                    plot_centre_blit(self.image_cache[4], [self.mypos[0], y])
                else:
                    self.image_cache[4] = create_circular_blit(
                        [self.mypos[0], y], self.diameter, 0, colour, [0, 0, 0], 200, False, 0)
            for child_node in self.children1:
                child_node.y_child_projection(limit, colour, y)
        return

    def max_min_freq(self, limit, min1, max1):
        """
        Return max min frequency
        """
        #self.calc_mypos()
        limit -= 1
        if(limit > 0):
            #if(self.bindu==False):
            min1 = min(min1, self.freq)
            max1 = max(max1, self.freq)
            for child_node in self.children1:
                min_max = child_node.max_min_freq(limit, min1, max1)
                if(min_max is not None):
                    min1 = min_max[0]
                    max1 = min_max[1]
            return [min1, max1]
        return [min1, max1]

    def depth_projection(self, limit, colour, dist, vertical):
        """
        Project children onto one axis
        """
        #self.calc_mypos()
        limit -= 1
        if(limit > 0):
            for child_node in self.children1:
                child_node.depth_projection(limit, colour, dist, vertical)
        else:
            if (vertical == True):
                pos = [self.mypos[0], dist]
                image_num = 6
            else:
                pos = [dist, self.mypos[1]]
                image_num = 7
            if(self.image_cache[image_num] != None):
                plot_centre_blit(self.image_cache[image_num], pos)
            else:
                self.image_cache[image_num] = create_circular_blit(
                    pos, self.diameter, 0, colour, [0, 0, 0], 200, False, 0)
        return

    def opencv_plot_gml(self, cv2, limit, image, photo_pos, inverse_gml=False):
        """
        Test function to plot a gml using opencv
        """
        top = 480
        x1 = int(self.mypos[0]-photo_pos[0])
        y1 = int(top-(self.mypos[1]-photo_pos[1]))
        limit -= 1
        if(limit > 0):
            for child_node in self.children1:
                if (child_node != None):
                    if(inverse_gml):
                        x1 = int(child_node.mypos[0]-photo_pos[0])
                        y1 = int(top-(child_node.mypos[1]-photo_pos[1]))
                    r = int(child_node.orbit_radius)
                    cv2.circle(image, (x1, y1), r, self.colour, 1)
                    child_node.opencv_plot_gml(
                        cv2, limit, image, photo_pos, inverse_gml)
        if(image is not None):
            cv2.imshow('frame', image)

    def gml_to_text(self, limit):
        """
        Function to convert GML to text revealing
        only the basic geometry.
        """
        if(self.parent == None):
            gml_text = "B1,"
        else:
            gml_text = ""
        gml_child_dictionary = {}
        limit -= 1
        child_count = 0
        if(limit > 0):
            if(len(self.children1) > 0):
                for child_node in self.children1:
                    if (child_node is not None):
                        phase = child_node.start_phase+0.001*child_count
                        gml_child_dictionary[phase] = child_node
                        child_count += 1
                sorted_children = sorted(
                    gml_child_dictionary.items(), key=lambda x: x[0])
                #print("Count:",child_count,"Sorted:",sorted_children)
                gml_text += str(child_count)+","
                for child_node in sorted_children:
                    if (child_node[1] != None):
                        gml_text += child_node[1].gml_to_text(limit)
            else:
                gml_text += "0,"
        return gml_text

    def closest_value(self, input_list, input_value):
        if(len(input_list) == 0):
            return -9999

        def difference(input_list): return abs(input_list - input_value)
        res = min(input_list, key=difference)
        return res

    def gml_line_plot(self, limit, match_frequency=True, fuzzy_match=False, depth=0):
        """
        Function to convert GML to text revealing
        only the basic geometry.
        """
        quantise_freq = 2
        depth += 1

        gml_child_dictionary = {}
        gml_freq_dictionary = {}
        limit -= 1
        child_count = 0
        if(limit > 0):
            if(len(self.children1) > 0):
                for child_node in self.children1:
                    if (child_node is not None):
                        phase = child_node.start_phase+0.001*child_count
                        gml_child_dictionary[phase] = child_node
                        child_count += 1
                sorted_children = sorted(
                    gml_child_dictionary.items(), key=lambda x: x[0])
                #print("Count:",child_count,"Sorted:",sorted_children)

                start_pos = None
                freq_list = []
                #positions=[]
                for child_node in sorted_children:
                    if (child_node[1] != None):
                        pos = child_node[1].mypos
                        if(match_frequency == True):
                            freq = child_node[1].freq
                        else:
                            freq = 1
                        if(fuzzy_match):
                            closest_freq = self.closest_value(freq_list, freq)
                            if(abs(closest_freq-freq) > quantise_freq):
                                freq_list.append(freq)
                                if freq not in gml_freq_dictionary:
                                    gml_freq_dictionary[freq] = []
                            else:
                                freq = closest_freq
                                #print("matched")
                            #print(freq,closest_freq)
                        if (not freq in gml_freq_dictionary):
                            gml_freq_dictionary[freq] = []
                        gml_freq_dictionary[freq].extend((pos[0], pos[1]))

                #print(gml_freq_dictionary.keys)

                for freq_key in gml_freq_dictionary:
                    #Append the start position to the end to complete a polygon
                    start_pos = gml_freq_dictionary[freq_key]
                    gml_freq_dictionary[freq_key].extend(
                        (start_pos[0], start_pos[1]))

                    #Check for singularities
                    if(len(gml_freq_dictionary[freq_key]) == 4):
                        gml_freq_dictionary[freq_key].extend(
                            (self.mypos[0], self.mypos[1]))

                #for freq in gml_freq_dictionary.keys()
                #print(gml_freq_dictionary)

                for freq_key in gml_freq_dictionary:
                    plot_lines(gml_freq_dictionary[freq_key], [
                               0.8, 0.2+depth/10, 0.8], 0.9, 1)

                for child_node in self.children1:
                    if (child_node != None):
                        child_node.gml_line_plot(
                            limit, match_frequency, fuzzy_match, depth)
        return


#This is outside the class to create the top level root node
def create_bindu(reset_count=True):
    """
    Create the Bindu point at the centre and top of the
    GML tree
    """
    parent_node = None
    bindu_node = GML_2D(
        'Bindu', 0.001, [255, 255, 255], 0, 0, None, parent=parent_node)
    if(reset_count == True):
        bindu_node.reset_osc_count()
        GMLBaseClass.osc_count += 1
    return bindu_node
