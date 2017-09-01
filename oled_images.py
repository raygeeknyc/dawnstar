width = disp.width
height = disp.height
image = Image.new('1', (width, height))
diameter = 10
iris_diameter = 3

def getDrawing(display):
    width = display.width
    height = display.height
    image = Image.new('1', (width, height))
    drawing = ImageDraw.Draw(image)
    return drawing

def drawEyeLookingLeft(drawing, top_left, diameter, iris_diameter):
    x,y = top_left
    drawing.ellipse((x, y, x+diameter, y+diameter), outline=255, fill=0)
    drawing.ellipse((x+1, y+diameter/2-iris_diameter/2, x+1+iris_diameter, (y+diameter/2-iris_diameter/2)+iris_diameter), outline=255, fill=255)
    
def drawEyeLookingRight(drawing, top_left, diameter, iris_diameter):
    x,y = top_left
    drawing.ellipse((x, y, x+diameter, y+diameter), outline=255, fill=0)
    drawing.ellipse((x+diameter-2-iris_diameter, y+diameter/2-iris_diameter/2, x+diameter-2, y+diameter/2), outline=255, fill=255)
    
def drawEyeLookingUp(drawing, top_left, diameter, iris_diameter):
    x,y = top_left
    drawing.ellipse((x, y, x+diameter, y+diameter), outline=255, fill=0)
    drawing.ellipse(x+diameter/2-iris_diameter/2, y+1, (x+diameter/2-iris_diameter/2)+iris_diameter, y+1+iris_diameter), outline=255, fill=255)

def drawEyeLookingDown(drawing, top_left, diameter, iris_diameter):
    x,y = top_left
    drawing.ellipse((x, y, x+diameter, y+diameter), outline=255, fill=0)
    drawing.ellipse(x+diameter/2-iris_diameter/2, y+diameter-2-iris_diameter, (x+diameter/2-iris_diameter/2)+iris_diameter, y+diameter-2), outline=255, fill=255)

def face_looking_right(drawing):
