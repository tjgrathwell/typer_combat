import pygame
from general import game_constants

def distfromground(rect, colliders):
    """ Evaluates distance from all screen sprites based on floating point position """
    smallest = game_constants.big_distance
    leftx = rect.left
    rightx = rect.right
    bottom = rect.bottom
    for sprite in colliders:
        if sprite.rect.left < rightx:
            if leftx < sprite.rect.right:
                if bottom <= sprite.rect.top:
                    dist = sprite.rect.top - bottom
                    if dist < smallest:
                        smallest = dist
    return smallest
    
def distfromceiling(rect, colliders):
    """ Evaluates distance from all screen sprites based on floating point position """
    smallest = game_constants.big_distance
    leftx = rect.left
    rightx = rect.right
    top = rect.top
    for sprite in colliders:
        if sprite.rect.left < rightx:
            if leftx < sprite.rect.right:
                if top <= sprite.rect.bottom:
                    dist = sprite.rect.bottom - top
                    if dist < smallest:
                        smallest = dist
    return smallest
    
def twopointrect((startx, starty), (destx, desty)):
    """ Get the rect that contains two arbitrary points """
    if starty < desty: # start is above dest
        if startx < destx:
            topleft = (startx, starty)
            bottomright = (destx, desty)
        else:
            topleft = (destx, starty)
            bottomright = (startx, desty)
    else: # dest is above start
        if startx < destx:
            topleft = (startx, desty)
            bottomright = (destx, starty)
        else: # topleft corner is 
            topleft = (destx, desty)
            bottomright = (startx, starty)
    width = bottomright[0] - topleft[0]
    height = bottomright[1] - topleft[1]
    return pygame.rect.Rect((topleft), (width, height))
    
def clearshot((startx, starty), (destx, desty), rectlist, depth = 3):
    """ True if there is a clear path from 'rect' to 'dest' """
    # Get all colliders contained within these two points
    indices = twopointrect((startx, starty), (destx, desty)).collidelistall(rectlist)
    rects = [rectlist[idx] for idx in indices]
    
    if len(rects) == 0: return True
    elif depth == 0: return False # Drilled as far down as i'm willing
    
    xdist = destx - startx
    ydist = desty - starty
    midpoint = (startx + xdist / 2, starty + ydist / 2)
    
    # Divide the RECTANGLE OF POSSIBILITY into two. Only pass on the rects that collided with the current one.
    r1 = clearshot((startx, starty), midpoint, rects, depth - 1)
    r2 = clearshot(midpoint, (destx, desty), rects, depth - 1)
    return (r1 and r2)
