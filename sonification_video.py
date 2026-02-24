# =========================
# Standard Library
# =========================
import argparse
import ctypes
import logging
from threading import Thread
from time import sleep
from ctypes import wintypes
import os

# =========================
# Third-Party Libraries
# =========================
import cv2
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import *
from kivy.uix.button import Button

# =========================
# Local Project Modules
# =========================
from Sonic_GML import *
from GML import *
from GML_analysis import *
from GML_tree_builder import *
from GML_invariant_detector import *
from GML_frequency_projection import *
from gl_text_drawing import *
from blit_functions import *
from colour_functions import *

class GMLSonificationApp(App):
    x = 100
    y = 100
    button1 = None
    button2 = None
    redraw = False
    rootNode = None
    text1 = None
    fbo = None
    offset = 0
    dir = -1
    loop_start = 100
    loop_speed = 0.4
    layers = 500
    geometry = 40
    geometry2 = 2
    geo = 101
    done = False
    start = False
    loop = loop_start
    cycle = 0
    photo_on = False
    reverse = False
    blank = True
    pause = False
    run_on = True
    log_music = True
    timer_loop = 0
    timer_max = 25
    tempo = 300
    music_scale = 23.5
    gml_timer_loop = 0
    gml_loop_max = 25
    gml_rate = 4
    args = None
    sonic = None
    tree_builder = None
    invariant_detector = None
    capturing_video = False
    sonic_thread = None
    plot_thread=None
    playing_sounds = False
    plotting_points = False

    def __init__(self, **kwargs):
        super(GMLSonificationApp, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, None)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        Window.bind(on_resize=self.on_window_resize)
        blit_functions_init(Window)
        GML_init()
        self.fbo = Fbo(size=Window.size, with_stencilbuffer=True)
        self.tree_builder = GML_tree_builder(False, self.button1)
        if(self.tree_builder.video_on == True):
            self.photo_on = False  # not self.photo_on
            self.redraw = True
            self.tree_builder.ppm_mode = 7  # Switch to PPM Pythagorean mode
            self.tempo = self.tree_builder.tempo
            self.gml_rate = 0
        else:
            self.tree_builder.ppm_mode = 0

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        self.redraw = False
        #keypress = pygame.key.get_pressed()
        if keycode[1] == 's':
            self.redraw = True
        elif keycode[1] == 't':
            self.layers += 1
            self.redraw = True
        elif keycode[1] == 'f':
            self.layers -= 1
            self.redraw = True
        elif keycode[1] == 'r':
            self.geometry += 1
            self.redraw = True
        elif keycode[1] == 'd':
            self.geometry -= 1
            self.redraw = True
        elif keycode[1] == 'q':
            self.geometry2 += 1
            self.redraw = True
        elif keycode[1] == 'w':
            self.geometry2 -= 1
            self.redraw = True
        elif keycode[1] == '1':
            self.offset += 0.1
            self.redraw = True
        elif keycode[1] == '2':
            self.offset -= 0.1
            self.redraw = True
        elif keycode[1] == 'p':
            self.tempo += 1
            #redraw=True
        elif keycode[1] == 'l':
            self.tempo -= 1
            #redraw=True
        elif keycode[1] == '3':
            self.reverse = True
            self.rootNode.set_reverse(True)
            self.gml_rate = 400
        elif keycode[1] == '4':
            self.gml_rate = 0
            self.cycle = 0
            self.rootNode.reset_phases(self.limit)
            self.rootNode.run1_areas(self.limit)
            self.rootNode.run1(self.limit)
            self.rootNode.gml_line_plot(100, False)

            self.sonic.all_midi_notes_off()
        elif keycode[1] == '5':
            self.reverse = False
            self.rootNode.set_reverse(False)
            self.gml_rate = 400
        elif keycode[1] == '6':
            self.sonic.increment_draw_mode(1, self.rootNode)
        elif keycode[1] == '7':
            self.tempo = 100
        elif keycode[1] == 'o':
            self.gml_rate += 1
        elif keycode[1] == 'k':
            self.gml_rate -= 1
        elif keycode[1] == 'i':
            self.sonic.increment_chord_size(+1)
        elif keycode[1] == 'j':
            self.sonic.increment_chord_size(-1)
        elif keycode[1] == 'u':
            self.sonic.increment_octaves(+1)
        elif keycode[1] == 'h':
            self.sonic.increment_octaves(-1)
        elif keycode[1] == 'z':
            self.photo_on = not self.photo_on
            self.redraw = True
        elif keycode[1] == 'x':
            self.reverse = not self.reverse
            self.rootNode.set_reverse(self.reverse)
        elif keycode[1] == 'c':
            self.pause = not self.pause
            self.rootNode.set_pause(self.pause)
        elif keycode[1] == 'm':
            self.blank = not self.blank
        elif keycode[1] == 'n':
            self.log_music = not self.log_music
            self.sonic.set_log_music(self.log_music)
        elif keycode[1] == '8':
            self.music_scale -= 0.1
            self.sonic.set_music_scale(self.music_scale)
        elif keycode[1] == '9':
            self.music_scale += 0.1
            self.sonic.set_music_scale(self.music_scale)
        elif keycode[1] == '-':
            self.tree_builder.increment_ppm_mode()
            self.redraw = True
        elif keycode[1] == 'b':
            self.run_on = not self.run_on
        elif keycode[1] == 'a':
            self.sonic.increment_gml_mode(1)
        elif keycode[1] == 'e':
            self.sonic.increment_draw_mode(1, self.rootNode)
        return True

    def on_window_resize(self, window, width, height):
        logging.info("[App Window  ] width="+str(width)+" height="+str(height))
        blit_functions_init(Window)
        GML_resize()
        self.redraw = True

    def button_callback(self, value):
        self.redraw = True

    def update(self, dt):
        if(self.button1 == None):
            self.button1 = Button(text="Main button")
            self.button1.bind(on_press=self.button_callback)
            blit_functions_canvas(self.button1.canvas, self.fbo)
            self.tree_builder.setButton(self.button1)

            self.read_setup()
            self.rootNode.print_tree()
            self.rootNode.set_draw_mode(4)
            self.rootNode.set_pause(False)
        else:
            pass
        if (self.button2 == None):
            self.button2 = Button(text="Frequency Phase Spectrum")

        if(self.loop > (self.geo+1) or self.loop < self.loop_start):
            self.dir = -self.dir
        self.loop += self.loop_speed*self.dir

        if (self.geometry2 > self.geometry):
           self.geometry2 = self.geometry
        if(self.geometry < 1):
           self.geometry = 1
        if(self.geometry2 < 1):
           self.geometry2 = 1
        if(self.layers < 1):
           self.layers = 1

        if(self.tempo <= 0):
           self.tempo = 0.1
        self.timer_max = 1000/self.tempo
        if(self.gml_rate <= 0):
           self.gml_rate = 0.1
        self.gml_loop_max = 1000/self.gml_rate

        if(self.blank == True):
            self.button1.canvas.clear()

        if (self.redraw == True or self.tree_builder.frame_ready()):
            self.rootNode.reset_run_counter()
            self.rootNode.reset_osc_count()
            self.dir = -1
            self.loop_start = self.layers
            self.loop_speed = 0.4
            self.geo = self.layers+1
            self.tree_builder.draw_photo(self.args["image"])
            self.rootNode = self.tree_builder.build_tree(self.geometry, False)
            self.redraw = False

        self.limit = int(self.loop)
        self.rootNode.reset_run_counter()

        if (self.photo_on == True):
            self.tree_builder.draw_photo(self.args["image"])

        if(self.run_on == True):
            self.rootNode.run1_areas(self.limit)
            self.rootNode.run1(self.limit)

            if(self.tree_builder.video_on):
                self.rootNode.gml_line_plot(100, True,True)
                new_tempo = (self.rootNode.run_counter()-30)*5
                if(new_tempo < 15):
                    new_tempo = 15
                if(new_tempo > 300):
                    new_tempo = 300
                self.tempo = new_tempo

            for depth in range(1, self.geometry):
                self.rootNode.depth_projection(
                    depth, [0, 255, 0], depth*10, True)
                self.rootNode.depth_projection(
                    depth, [255, 0, 0], depth*10, False)
            if(self.invariant_detector != None):
                self.invariant_detector.detect(self.rootNode, self.limit)
            freq_phases = freq_projection(self.rootNode, 0, 100)
            norm_freq_phases = normalise_freqs(freq_phases)
            #print(norm_freq_phases)
            if(self.button2 is not None):
                plot_freq_phases(self.button1.canvas,self.text1,300,norm_freq_phases, [0, 255, 200], transparency=1.0, width=2.0,
                     height=40, screen=None) #,self.button2.canvas)

            self.text1.drawText(self.button1.canvas, 340, 955,
                                "Control Panel for Beyond Quantum Computer",32)
            self.text1.drawText(self.button1.canvas, 340, 925,
                                "Retrieving Geometric Invariants as Polyatomic Time Crystal", 24)


        self.gml_timer_loop += 1
        if(self.gml_timer_loop >= self.gml_loop_max):
           self.gml_timer_loop = 0
           if(self.run_on == True and self.pause == False):
              if(self.reverse == True):
                 self.cycle -= 1
              else:
                 self.cycle += 1
           self.rootNode.set_pause(self.pause)
        else:
           self.rootNode.set_pause(True)

        self.sonic.circle_notes()

        if(self.text1 == None):
            self.text1 = FreeDrawText()

        self.text1.drawText(self.button1.canvas, 10, 10,
                            "Defined Clocks: "+str(self.rootNode.oscillators()), 18)
        self.text1.drawText(self.button1.canvas, 10, 30,
                            "Clocks Running: "+str(self.rootNode.run_counter()), 18)
        self.text1.drawText(self.button1.canvas, 10, 50,
                            "Cycle: "+str(self.cycle), 18)
        self.text1.drawText(self.button1.canvas, 10, 70,
                            "Layers: "+str(round(self.layers, 2)), 18)
        self.text1.drawText(self.button1.canvas, 10, 90,
                            "Geometry: "+str(int(self.geometry)), 18)
        self.text1.drawText(self.button1.canvas, 10, 110,
                            "Tempo: "+str(int(self.tempo)), 18)
        self.text1.drawText(self.button1.canvas, 10, 130,
                            "GML Rate: "+str(int(self.gml_rate)), 18)
        self.text1.drawText(self.button1.canvas, 10, 1150,
                            "PPM mode: "+self.tree_builder.ppm_mode_text(), 38)
        self.text1.drawText(self.button1.canvas, 10, 190,
                            "Dimensions: "+str(self.rootNode.dimensions()), 18)
        self.sonic.drawText(self.text1, self.button1.canvas, 210)

        self.tree_builder.capture_from_camera()

        return self.button1

    def thread_sonic_player(self, name):
        logging.info("[Sonic Thread] Starting Sonification")
        self.playing_sounds = True
        while(self.playing_sounds):
            self.timer_loop += 1
            if(self.timer_loop >= self.timer_max):
                self.timer_loop = 0
                #print(self.timer_loop)
                if(self.run_on == True):
                    self.sonic.play_sonic_sequence(self.rootNode)
            sleep(0.02)
        logging.info("[Sonic Thread] Stopping Sonification")


    def thread_plotter(self, name):
        logging.info("[Plot Thread ] Starting 3D Plot")
        self.plotting_points = True
        while(self.plotting_points):
            draw_3d_plot()
            #draw_contour_plot()
            logging.info("[Plot Thread ] Plotting")
            sleep(0.6)
            print("plot thread")
            #plt.show()
        logging.info("[Plot Thread ] Stopping 3D Plot")

    def read_setup(self):
        """
        Read the startup arguments from the command line
        """
        self.sonic = Sonic_GML()
        if(self.tree_builder.video_on == True):
            self.sonic.phase_advance = self.tree_builder.sonic_phase_advance

        self.sonic.all_midi_notes_off()
        self.sonic.set_music_scale(self.music_scale)
        # construct the argument parser and parse the arguments
        ap = argparse.ArgumentParser()
        ap.add_argument("-i", "--image", required=False,
                        help="Path to the image")
        ap.add_argument("-s", "--size", required=False, help="size")
        ap.add_argument("-r", "--radius", required=False, help="radius")
        ap.add_argument("-z", "--capture_window", required=False, help="capture_window")
        self.args = vars(ap.parse_args())

        if(self.args["image"] is not None):
            # load the image, clone it for output, and then convert it to grayscale
            image = cv2.imread(self.args["image"])
            #scale= image.shape[1]/(screen_width-40)
            scale = 1
            dim = (int(image.shape[1]/scale), int(image.shape[0]/scale))
            print(str(int(scale))+" "+str(dim))

            output = image.copy()

            size = float(self.args["size"])
            rad = float(self.args["radius"])

            self.tree_builder.video_on = False
            self.tree_builder.set_circle_detect_dimensions(size, rad)
            self.tree_builder.add_circlular_features(image, dim, size, rad)
            self.tree_builder.draw_photo(self.args["image"])
        else:
            print("Video mode")
            self.tree_builder = GML_tree_builder(True, self.button1)
            self.tree_builder.video_on = True
            print("Running invariant detector")
            self.invariant_detector = GML_invariant_detector()
            self.tree_builder.set_circle_detect_dimensions(10, 120)
            self.sonic.draw_mode = 6
            #Prime with video
            self.tree_builder.capture_from_camera()

        if (self.args["capture_window"] is not None):
            window_name = str(self.args["capture_window"].strip('\"'))
            print("Window",window_name)
            self.tree_builder.window_video_capture=window_name
            #gw.getAllTitles()
            user32 = ctypes.windll.user32
            handle = user32.FindWindowW(None, window_name)
            rect = wintypes.RECT()
            ff = ctypes.windll.user32.GetWindowRect(handle, ctypes.pointer(rect))
            print(rect.left, rect.top, rect.right, rect.bottom)
            print(ff)
            self.tree_builder.window_video_capture_handle =[rect.left, rect.top, rect.right, rect.bottom]


        self.rootNode = self.tree_builder.build_tree(1000, True)

        #print("Clocks: ",clocks)
        if(self.text1 == None):
            self.text1 = FreeDrawText()
        print("Clocks: ", self.rootNode.oscillators())
        self.text1.drawText(self.button1.canvas, 10, 10,
                            "Clocks "+str(self.rootNode.oscillators()), 16)

        if(self.tree_builder.video_on == True):
            self.rootNode.set_oscillator_speed(1.00)
        else:
            self.rootNode.set_oscillator_speed(1.00)

        self.sonic_thread = Thread(target=self.thread_sonic_player, args=(1,))
        self.sonic_thread.start()
        self.plot_thread = Thread(target=self.thread_plotter, args=(1,))
        self.plot_thread.start()


class OpenGMLSonificationApp(App):
    app = None

    def on_stop(self):
        if self.app is not None:
            self.app.run_on = False
            self.app.playing_sounds = False
            self.app.capturing_video = False
            self.app.plotting_points = None

        if self.app.sonic_thread is not None:
            self.app.sonic_thread.join()

        if self.app.plot_thread is not None:
            self.app.plot_thread.join()

        del self.app.tree_builder
        self.app.invariant_detector.stop()

    def build(self):
        # Core system initialization
        GML_init()
        Sonic_GML_init()

        # App creation
        self.app = GMLSonificationApp()
        Clock.schedule_interval(self.app.update, 0.005 / 60.0)

        return self.app.update(0.0)

if __name__ == '__main__':
    os.makedirs("freq_data", exist_ok=True)
    OpenGMLSonificationApp().run()
    Sonic_GML_quit()
exit()
