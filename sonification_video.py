# =========================
# Standard Library
# =========================
import logging
from threading import Thread
from time import sleep
import os
import sys
import subprocess


def _list_visible_windows_cli():
    import win32gui

    windows = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and title.strip():
                windows.append((hwnd, title))

    win32gui.EnumWindows(callback, None)
    return windows


def _prompt_capture_config_cli():
    windows = _list_visible_windows_cli()

    if len(windows) == 0:
        cam_input = input("No windows found. Camera index (default 0): ").strip()
        try:
            camera_index = int(cam_input) if cam_input else 0
        except ValueError:
            camera_index = 0
        return {"video_source": "camera", "camera_index": camera_index, "selected_hwnd": None}

    print("\nAvailable Windows:\n")
    for i, (hwnd, title) in enumerate(windows):
        print(f"[{i}] {title}")
    print("[c] Camera feed")

    while True:
        selection = input("\nSelect window number or 'c' for camera: ").strip().lower()
        if selection == "c":
            cam_input = input("Camera index (default 0): ").strip()
            try:
                camera_index = int(cam_input) if cam_input else 0
            except ValueError:
                print("Invalid camera index, using 0")
                camera_index = 0
            return {"video_source": "camera", "camera_index": camera_index, "selected_hwnd": None}

        try:
            idx = int(selection)
            hwnd, title = windows[idx]
            print(f"\nSelected: {title}")
            return {"video_source": "window", "camera_index": 0, "selected_hwnd": hwnd}
        except (ValueError, IndexError):
            print("Invalid selection, try again.")


def _capture_config_from_env():
    source = os.environ.get("SONI_VIDEO_SOURCE", "window")
    cam_raw = os.environ.get("SONI_CAMERA_INDEX", "0")
    hwnd_raw = os.environ.get("SONI_SELECTED_HWND", "")

    try:
        camera_index = int(cam_raw)
    except ValueError:
        camera_index = 0

    selected_hwnd = None
    if hwnd_raw not in ("", "None", None):
        try:
            selected_hwnd = int(hwnd_raw)
        except ValueError:
            selected_hwnd = None

    return {
        "video_source": source,
        "camera_index": camera_index,
        "selected_hwnd": selected_hwnd,
    }


if __name__ == '__main__' and os.environ.get("SONI_CAPTURE_READY") != "1":
    capture_config = _prompt_capture_config_cli()
    child_env = os.environ.copy()
    child_env["SONI_CAPTURE_READY"] = "1"
    child_env["SONI_VIDEO_SOURCE"] = capture_config["video_source"]
    child_env["SONI_CAMERA_INDEX"] = str(capture_config["camera_index"])
    child_env["SONI_SELECTED_HWND"] = str(capture_config["selected_hwnd"])
    result = subprocess.run([sys.executable, __file__], env=child_env)
    sys.exit(result.returncode)

# =========================
# Third-Party Libraries
# =========================
import cv2
from kivy.app import App
from kivy.clock import Clock
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
    capture_config = None
    kivy_window = None

    def __init__(self, capture_config=None, **kwargs):
        super(GMLSonificationApp, self).__init__(**kwargs)
        self.capture_config = capture_config or {}
        from kivy.core.window import Window
        self.kivy_window = Window
        self._keyboard = self.kivy_window.request_keyboard(self._keyboard_closed, None)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.kivy_window.bind(on_resize=self.on_window_resize)
        blit_functions_init(self.kivy_window)
        GML_init()
        self.fbo = Fbo(size=self.kivy_window.size, with_stencilbuffer=True)
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
        blit_functions_init(window)
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

        self.tree_builder.capture_from_window()

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
        self.args = {"image": None}

        print("Video mode")
        source = self.capture_config.get("video_source", "window")
        camera_index = self.capture_config.get("camera_index", 0)
        selected_hwnd = self.capture_config.get("selected_hwnd", None)
        self.tree_builder = GML_tree_builder(
            True,
            self.button1,
            video_source=source,
            camera_index=camera_index,
            selected_hwnd=selected_hwnd,
        )
        self.tree_builder.video_on = True
        print("Running invariant detector")
        self.invariant_detector = GML_invariant_detector()
        self.tree_builder.set_circle_detect_dimensions(10, 120)
        self.sonic.draw_mode = 6
        #Prime with video
        self.tree_builder.capture_from_window()

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

    def __init__(self, capture_config=None, **kwargs):
        super(OpenGMLSonificationApp, self).__init__(**kwargs)
        self.capture_config = capture_config or {}

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
        self.app = GMLSonificationApp(capture_config=self.capture_config)
        Clock.schedule_interval(self.app.update, 0.005 / 60.0)

        return self.app.update(0.0)

if __name__ == '__main__':
    os.makedirs("freq_data", exist_ok=True)
    capture_config = _capture_config_from_env()
    OpenGMLSonificationApp(capture_config=capture_config).run()
    Sonic_GML_quit()
exit()
