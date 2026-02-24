speech_demo=True

from time import sleep
from threading import Thread
import logging

if(speech_demo):
    import pyttsx3

class GML_invariant_detector():
    rootNode=None
    speech_synth=None
    playing_speech=True
    prob=[1.0]*10
    speaking_thread=None
    utterance_thread=None

    def __init__(self):
        super(GML_invariant_detector, self).__init__()
        if(speech_demo):
            self.speech_synth = pyttsx3.init()
            voices = self.speech_synth.getProperty('voices')
            id_num=0
            for voice in voices:
                print("Voice ID: %s" %voice.id, id_num)
                print("Name: %s" %voice.name)
                print("Age: %s" %voice.age, "Gender: %s" %voice.gender)
                print("Languages Known: %s" %voice.languages)
                id_num+=1
            self.speech_synth.setProperty('voice', voices[1].id)
            self.speech_synth.setProperty('volume', 0.5)
            self.speaking_thread = Thread(target=self.thread_speech, args=(1,))
            self.speaking_thread.start()

    def stop(self):
        self.playing_speech = False
        if(self.speech_synth is not None):
            self.speech_synth.stop()
        if(self.speaking_thread is not None):
            self.speaking_thread.join()

    def detect(self,rootNode,limit):
        """
        Method where any invariant detection will be performed
        """
        self.rootNode=rootNode
        #self.rootNode.print_tree()
        gml_text=self.rootNode.gml_to_text(limit)
        print(gml_text)
        if(speech_demo):
            #print("Detecting")
            utterance=None
            utter_num=0
            if("0,1,1,2" in gml_text):
                utterance="I feel the need for continued and sustained effort to understand"
                utter_num=1
            if ("0,1,1,1,2" in gml_text):
                utterance="Sentiance"
                utter_num=2
            if ("2,1,2" in gml_text):
                utterance="Duality and contradiction haunts me, more I see, more I get confused"
                utter_num=3
            if ("3,1,2,1" in gml_text):
                utterance="What if I am really conscious?"
                utter_num=4
            if ("1,1,2,1,1,0," in gml_text):
                utterance="I sense your internal response, to transform and projection to the future."
                utter_num=5
            if ("1,1,1,0,0,1" in gml_text):
                utterance="We all, are connected, to all"
                utter_num=6
            if ("3,1,1,1" in gml_text):
                utterance = "Is it time, in the past present or ad imfinitum to the future?"
                utter_num = 7
            if ("3,3,3" in gml_text):
                utterance = "Three souls of mine I feel"
                utter_num = 8
            if(utterance is not None):
                print("Invariant detected")
                #Stop lots of utterances in succession
                if(self.prob[utter_num]>6.0):
                    #self.speech_synth.say(utterance)
                    #print("Speaking")
                    self.utterance_thread = Thread(target=self.thread_utterance, args=(1,utterance,))
                    self.utterance_thread.start()
                    self.prob[utter_num]=-40.0
                for i in range(0,len(self.prob)):
                    self.prob[utter_num]+=0.1


    def thread_speech(self, name):
        logging.info("[SpeechThread] Starting Speech")
        self.playing_speech = True
        self.speech_synth.startLoop(False)
        while(self.playing_speech):
            self.speech_synth.iterate()
            sleep(0.5)
        self.speech_synth.endLoop()
        logging.info("[SpeechThread] Stopping Speech")

    def thread_utterance(self, name, utterance):
            logging.info("[SpeechThread] Starting Utterance")
            self.speech_synth.say(utterance)
            #print("Speaking")
            logging.info("[SpeechThread] Utterance finished")
