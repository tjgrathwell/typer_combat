# PYOPENGLTEST - a prototype

# The hardest part of integrating this is going to be getting something that can display text

# STAGE 1: Make a texture that's just all the letters from a font rendered

# STAGE 2: Make sure the u-v coords for all the individual letters in the font are stored in some suitable structure

# STAGE 3: Make a function that can spit out a whole word just by drawing a series of quads from this big block of textures

# This won't look right initially, because RenderText knows things about character spacing that my function does not know. For instance, g and r are way closer than r and a.
# but as a benefit, this will give me control over getting pixel-perfect word typeover rather than the fidgety movey-around type I'm getting now

# Might be able to get away with generating & throwing away textures of prerendered text, but a memory leak is undoubtable

# Packing all the individual character images into a single texture will be a similar issue

(SCREEN_WIDTH, SCREEN_HEIGHT) = (640,480)

import pygame, sys, random, math, time, string, os
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *

def loadImage(image):
    texture = pygame.image.load(image)
    w = texture.get_width()
    h = texture.get_height()
    return pygame.image.tostring(texture,"RGBA",1), w, h

def makeTexture(textureBytes,w,h):
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D( GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, textureBytes )
    return texture

def gl_init((width, height)):
    if height==0:
        height=1
    glViewport(0, 0, width, height)
    
    # Window-sized ortho projection... sucks for resizability but I don't think that ever worked well
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT);

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Blend together sprites & stuff with alpha. Shit needs to be drawn painter-style to get this workin'.
    glEnable (GL_BLEND);
    glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    
    # Textures are a good use of time
    glEnable(GL_TEXTURE_2D)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    
    glClearColor(1.0, 1.0, 1.0, 0.0)
    glClearDepth(1.0)
    
    # Not sure about these gentlemen.
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_ALPHA_TEST)
    glDepthFunc(GL_LEQUAL)
    glAlphaFunc(GL_NOTEQUAL, 0.0)
        
class TexturedQuad:
    def __init__(self,data):
        if hasattr(data, "get_buffer"):
            self.w = data.get_width()
            self.h = data.get_height()
            self.texture_id = makeTexture(pygame.image.tostring(data,"RGBA",1), self.w, self.h)
        else:
            (surf, self.w, self.h) = loadImage(data)
            self.texture_id = makeTexture(surf, self.w, self.h)
        
    def draw(self,(x,y)):
        gl_drawrect(Rect(x,y,self.w,self.h),self.texture_id)
    
class G:
    boundtexture = None
def gl_draw_textured_quad(position_rect, texture_rect=None):
    x, y, w, h = position_rect.left, position_rect.top, position_rect.width, position_rect.height
    if (not texture_rect):
        umin, vmin, umax, vmax = 0,0,1,1
    else:
        umin = texture_rect.left/256.0
        vmin = 1-texture_rect.top/256.0
        umax = texture_rect.right/256.0
        vmax = 1-texture_rect.bottom/256.0
    
    # Singel drawrect calls are okay for starters, but eventually we might want to pack this into a display list for all quads on screen
    # but maybe not? how many quads will there be on screen, 50? doesn't much compare to 30,000 triangles...
    glTexCoord2f(umin, vmin);
    glVertex3f(x,     SCREEN_HEIGHT - y,     1.0) # Top Left
    glTexCoord2f(umin, vmax);
    glVertex3f(x,     SCREEN_HEIGHT - y - h, 1.0) # Bottom Left
    glTexCoord2f(umax, vmax);
    glVertex3f(x + w, SCREEN_HEIGHT - y - h, 1.0) # Bottom Right    
    glTexCoord2f(umax, vmin);
    glVertex3f(x + w, SCREEN_HEIGHT - y,     1.0) # Top  Right
    
def map_letters():
    alphabet_surface = pygame.Surface((256,256), SRCALPHA)
    alphabet_surface.fill((255,255,255,0))
    font = pygame.font.Font('galaxy_1.ttf', 24)
    startx, starty, maxheight = 0,0,0
    
    letter_rects = {}
    
    for letter in string.printable:
        letter_surface = font.render(letter, 1, (0, 0, 0))
        if (startx + letter_surface.get_width() > alphabet_surface.get_width()):
            starty += maxheight
            startx = maxheight = 0
        alphabet_surface.blit(letter_surface, (startx, starty))
        letter_rects[letter] = Rect(startx, starty, letter_surface.get_width(), letter_surface.get_height())
        startx += letter_surface.get_width()
        maxheight = max(letter_surface.get_height(), maxheight)
    return alphabet_surface, letter_rects
        
def gl_drawword(letter_map, letter_texture_id, word, y=0):
    startx, starty = 0,y
    
    if letter_texture_id is not None and letter_texture_id != G.boundtexture:
        glBindTexture(GL_TEXTURE_2D, letter_texture_id)
        G.boundtexture = letter_texture_id
        print 'i bind your texture'
    
    glBegin(GL_QUADS)
    for letter in word:
        this_letter = letter_map[letter]
        position_rect = Rect(startx, starty, this_letter.width, this_letter.height)
        gl_draw_textured_quad(position_rect, letter_map[letter])
        startx += position_rect.width
    glEnd()
        
def main(argv=sys.argv):
    import py2exeeggs
    py2exeeggs.loadEggs()

    pygame.init()
    pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT),OPENGL|DOUBLEBUF)
    gl_init((SCREEN_WIDTH,SCREEN_HEIGHT))
    pygame.display.set_caption('pyogl-test prototype')
    
    letter_texture, letter_map = map_letters()
    letter_texture_id = makeTexture(pygame.image.tostring(letter_texture,"RGBA",1), letter_texture.get_width(), letter_texture.get_height())

    keys_down = {}
    move_speed = 5
    ticks = 0
    curtex = 0
    object_pos = [0,0]
    
    start_time = time.time()
    frames = 0
    CameraPos = [0,0,0]
    
    while True: # The Full Game Loop
        for event in (pygame.event.get()):
            if event.type == QUIT:
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    sys.exit()
                else:
                    keys_down[event.key] = 1
            if event.type == KEYUP:
                del keys_down[event.key]
        if K_UP in keys_down:
            CameraPos[1] -= move_speed
        if K_DOWN in keys_down:
            CameraPos[1] += move_speed
        if K_LEFT in keys_down:
            CameraPos[0] -= move_speed
        if K_RIGHT in keys_down:
            CameraPos[0] += move_speed
        # 2d
        #pygame.display.update()
        # 3d

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Camera Position/Orient
        #glRotatef(-CameraRotate[1],1,0,0)
        #glRotatef( CameraRotate[0],0,1,0)
        glTranslatef(CameraPos[0],-CameraPos[1],0)
        
        text=   ['This string is the best string ever.',
                 'But this string is also alright.',
                 'Don\'t discount this string in your evaluation.',
                 'This string should not be considered.',
                 'This string is the best string ever as well.',
                 'This string is cool sometimes but not right now.',
                 'This screen has a lot of words on it.',
                 'This string is filling up space.',
                 'This string is well within your polygon budget',
                 'Only a fool would enjoy coding this project.']
        i = 0
        for word in text:
            gl_drawword(letter_map, letter_texture_id, word, i)
            i += 30

        pygame.display.flip()
        
        # ticks += 1
        # if (ticks % 10) == 0:
            # curtex += 1
            # curtex %= len(quads)
            
        frames += 1
        if (frames % 100) == 0:
            print "fps: " + str(frames/(time.time() - start_time))

if __name__ == '__main__':
    main()