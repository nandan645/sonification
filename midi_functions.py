from kivy.clock import Clock
import time
import logging

C = 74
MAX = 127
fs = None
sfid = None
midi_channels = 64
instruments = None

instrument_list = ['Acoustic Grand Piano', 'Bright Acoustic Piano', 'Electric Grand Piano', 'Honky-tonk Piano', 'Electric Piano 1', 'Electric Piano 2', 'Harpsichord', 'Clavinet',
                   'Celesta', 'Glockenspiel', 'Music Box', 'Vibraphone', 'Marimba', 'Xylophone', 'Tubular Bells', 'Dulcimer',
                   'Drawbar Organ', 'Percussive Organ', 'Rock Organ', 'Church Organ', 'Reed Organ', 'Accordion', 'Harmonica', 'Tango Accordion',
                   'Acoustic Guitar (nylon)', 'Acoustic Guitar (steel)', 'Electric Guitar (jazz)', 'Electric Guitar (clean)', 'Electric Guitar (muted)', 'Overdriven Guitar', 'Distortion Guitar', 'Guitar Harmonics',
                   'Acoustic Bass', 'Electric Bass (finger)', 'Electric Bass (pick)', 'Fretless Bass', 'Slap Bass 1', 'Slap Bass 2', 'Synth Bass 1', 'Synth Bass 2',
                   'Violin', 'Viola', 'Cello', 'Contrabass', 'Tremolo Strings', 'Pizzicato Strings', 'Orchestral Harp', 'Timpani',
                   'String Ensemble 1', 'String Ensemble 2', 'Synth Strings 1', 'Synth Strings 2', 'Choir Aahs', 'Voice Oohs', 'Synth Choir', 'Orchestra Hit',
                   'Trumpet', 'Trombone', 'Tuba', 'Muted Trumpet', 'French Horn', 'Brass Section', 'Synth Brass 1', 'Synth Brass 2',
                   'Soprano Sax', 'Alto Sax', 'Tenor Sax', 'Baritone Sax', 'Oboe', 'English Horn', 'Bassoon', 'Clarinet',
                   'Piccolo', 'Flute', 'Recorder', 'Pan Flute', 'Blown Bottle', 'Shakuhachi', 'Whistle', 'Ocarina',
                   'Lead 1 (square)', 'Lead 2 (sawtooth)', 'Lead 3 (calliope)', 'Lead 4 (chiff)', 'Lead 5 (charang)', 'Lead 6 (voice)', 'Lead 7 (fifths)', 'Lead 8 (bass + lead)',
                   'Pad 1 (new age)', 'Pad 2 (warm)', 'Pad 3 (polysynth)', 'Pad 4 (choir)', 'Pad 5 (bowed)', 'Pad 6 (metallic)', 'Pad 7 (halo)', 'Pad 8 (sweep)',
                   'FX 1 (rain)', 'FX 2 (soundtrack)', 'FX 3 (crystal)', 'FX 4 (atmosphere)', 'FX 5 (brightness)', 'FX 6 (goblins)', 'FX 7 (echoes)', 'FX 8 (sci-fi)',
                   'Sitar', 'Banjo', 'Shamisen', 'Koto', 'Kalimba', 'Bagpipe', 'Fiddle', 'Shanai',
                   'Tinkle Bell', 'Agogo', 'Steel Drums', 'Woodblock', 'Taiko Drum', 'Melodic Tom', 'Synth Drum', 'Reverse Cymbal',
                   'Guitar Fret Noise', 'Breath Noise', 'Seashore', 'Bird Tweet', 'Telephone Ring', 'Helicopter', 'Applause', 'Gunshot']


def midi_init():
    """
    Initialise Midi functions
    """
    global port, fs, sfid, instruments, midi_channels
    port = 0
    #fs = fluidsynth.Synth()
    if fs is not None:
        fs.start()
        time.sleep(1)
        instruments = [75, 75, 75, 71, 72, 76, 77, 78,75, 75, 75, 71, 72, 76, 77, 78,75, 75, 75, 71, 72, 76, 77, 78]
        chan = 0
        for instr in instruments:
            fs.program_select(chan, sfid, 0, instr)
            chan += 1
        midi_channels = chan
        #print("MIDI Channels:",chan)
        logging.info("[MIDI        ] "+str(chan)+" channels enabled")

        #Original
        roomsize = 1.8
        damping = 0.001
        width = 5.8
        level = 7.5
        fs.set_reverb(roomsize, damping, width, level)
        logging.info("[Fluid Synth ] Fluid synth enabled")


def midi_instrument(instrument, bank=0, midi_chan=0):
    global fs, sfid
    fs.program_select(midi_chan, sfid, bank, instrument)


def midi_quit():
    """
    Function to close Midi channel on exit
    """
    global fs
    music = 0
    if fs is not None:
        fs.delete()
    del fs


def all_midi_off(counter=3):
    """
    Stop all midi notes
    """
    global midi_channels
    for chan in range(0, midi_channels-1):
        for note in range(0, 127):
            if (fs is not None):
                fs.noteoff(chan, note)
    counter -= 1
    if (counter > 0):
        Clock.schedule_once(lambda dt: all_midi_off(counter), 0.1)


def midi_on(prev_note=[C], notes_in=[C], vol=[MAX], panning=[50]):
    """
    Trigger an external midi note
    """
    global fs, instruments, midi_channels
    pan_ctrl = 10  # PAN_MSB
    bal_ctrl = 8
    note = list(dict.fromkeys(notes_in))  # remove duplicates
    i = 0
    for n in note:
        no = round(n)

        chan = no % midi_channels
        frac_note = round((no-n)*4096)
        volume = int(vol[i])
        pan = panning[i]
        if(volume < 0):
            volume = 0
        for n1 in prev_note:
            if(no == round(n1)):
                #Flag as not to play again
                """ This prevents note retrigger if uncommented"""
                if(chan % 5 != 0):
                    n = 0  # Only continuous on some channels
                pass
        #if(n > 0):
            #pan=chan*int(120/midi_channels)+7
        if instruments is not None and n > 0:
            gm_instrument_num = instruments[chan]
            print("Note:", no, " Pitch:", frac_note, " Chan:", chan, " Pan:", pan, "Vol:",
                  volume, " GM_MIDI:", gm_instrument_num, "=", instrument_list[gm_instrument_num])
            # 74 is middle C, 127 is "how loud" - max is 127
            if (fs is not None):
                fs.noteon(chan, no, volume)
                fs.pitch_bend(chan, frac_note)
                fs.cc(chan, pan_ctrl, pan)
                fs.cc(chan, bal_ctrl, pan)
        i += 1


def midi_off(note=[C], note2=[C], volume=MAX):
    """
    Disable an external midi note
    """
    if (note != None):
        for n in note:
            no = round(n)
            chan = no % midi_channels
            #Check for notes that should not be off
            for n1 in note2:
                if(no == round(n1)):
                    #Flag as not to clear
                    n = 0
            if(n > 0):
                if (fs is not None):
                    fs.noteoff(chan, no)
