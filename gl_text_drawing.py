from kivy.core.text import Label as CoreLabel
from kivy.graphics import *

prev_text=""
text_texture=None

class FreeDrawText():
    prev_text=""
    text_texture=None

    def __init__(self):
        self.prev_text=""
        self.text_texture=None

    def drawText(self,canvas, x, y, disp_text, pts,colour=[1,1,1,1]):
        """
        Draw text at a given position on the screen setting the font size
        """
        if(self.text_texture==None or disp_text!=self.prev_text):
            label = CoreLabel(text=disp_text, font_size=str(pts))
            label.refresh()
            self.text_texture = label.texture
            #print(disp_text)
            self.prev_text=disp_text
        with canvas:
            Color(colour)
        canvas.add(Rectangle(size=self.text_texture.size, pos=[x,y], texture=self.text_texture))
        #canvas.ask_update()

    def drawTextRotate(self,canvas, x, y, disp_text, pts,colour=[1,1,1,1], angle=0):
        """
        Draw text at a given position on the screen setting the font size
        """
        if(self.text_texture==None or disp_text!=self.prev_text):
            label = CoreLabel(text=disp_text, font_size=str(pts))
            label.refresh()
            self.text_texture = label.texture
            #print(disp_text)
            self.prev_text=disp_text
        with canvas:
            PushMatrix()
            Rotate(angle=angle, origin=(x, y))
            Color(colour)
            canvas.add(Rectangle(size=self.text_texture.size, pos=[x,y], texture=self.text_texture))
            PopMatrix()
        #canvas.ask_update()