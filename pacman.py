import pygame
from pygame.locals import *
from vector import Vector2
from constants import *
from entity import Entity
from sprites import PacmanSprites

import numpy as np
import math

class Pacman(Entity):
    def __init__(self, node):
        Entity.__init__(self, node )
        self.name = PACMAN    
        self.color = YELLOW
        self.direction = LEFT

        self.setBetweenNodes(LEFT)
        self.alive = True
        self.setSpeed(100)
        self.sprites = PacmanSprites(self)
        
        self.target_point = Vector2(12, 26) 
        self.target_set = True
        self.target_able = True
        
        self.curmap = None
        self.basemap = self.basemap()
        
    def reset(self):
        Entity.reset(self)
        self.direction = LEFT
        self.setBetweenNodes(LEFT)
        self.alive = True
        self.image = self.sprites.getStartImage()
        self.sprites.reset()

    def die(self):
        self.alive = False
        self.direction = STOP

    def update(self, dt, ghosts, pelletList):	
        self.sprites.update(dt)
        self.position += self.directions[self.direction]*self.speed*dt
                    
        self.updatemap(ghosts)
        direction = self.direction
        if (    (self.position.x % 16 < 1.7 or self.position.x % 16 > 14.3)
            and (self.position.y % 16 < 1.7 or self.position.y % 16 > 14.3)     ):  # 3.4 = 1 frame
            
            if not self.target_set:
                self.i_pellet = 0
                pelletList[self.i_pellet].color = RED
                self.target_point = pelletList[self.i_pellet].position.__div__(16)
                self.target_set = True
                
            if not self.target_able:
                pelletList[0].color = WHITE
                # pelletList[self.i_pellet].color = WHITE
                for i in pelletList:
                    i.color = WHITE
                self.i_pellet = np.random.randint(pelletList.__len__())
                pelletList[self.i_pellet].color = RED
                self.target_point = pelletList[self.i_pellet].position.__div__(16)
                self.target_able = True
                
            direction = self.a_star(self.target_point)
            
            if direction is None:
                direction = STOP
        
        
        if self.overshotTarget():
            self.node = self.target
            if self.node.neighbors[PORTAL] is not None:
                self.node = self.node.neighbors[PORTAL]
            self.target = self.getNewTarget(direction)
            if self.target is not self.node:
                self.direction = direction
            else:
                self.target = self.getNewTarget(self.direction)

            if self.target is self.node:
                self.direction = STOP
            self.setPosition()
        else: 
            if self.oppositeDirection(direction):
                self.reverseDirection()

    def getValidKey(self):
        key_pressed = pygame.key.get_pressed()
        if key_pressed[K_UP]:
            return UP
        if key_pressed[K_DOWN]:
            return DOWN
        if key_pressed[K_LEFT]:
            return LEFT
        if key_pressed[K_RIGHT]:
            return RIGHT
        return STOP  

    def eatPellets(self, pelletList):
        for pellet in pelletList:
            if self.collideCheck(pellet):
                pelletList.sort(key = lambda x : self.sqrtEucDis(self.TwoPointDis(self.position, x.position)))
                return pellet
        return None    
    
    def collideGhost(self, ghost):
        return self.collideCheck(ghost)

    def collideCheck(self, other):
        d = self.position - other.position
        dSquared = d.magnitudeSquared()
        rSquared = (self.collideRadius + other.collideRadius)**2
        if dSquared <= rSquared:
            return True
        return False


#--------------------------------------------------------
    def basemap(self):
        list = []
        f = open("maze1.txt", "r")
        
        row = NROWS
        while row > 0:
            a = f.readline()
            for x in a:
                if (x != " " and x != '\n'): 
                    if (x != '.' and x != '+' and x != 'p' and x != '-' and x != '|' and x != 'n'): list.append(1)
                    else: list.append(0)
            row-=1
        f.close()

        arr = np.array(list)
        arr = arr.reshape(NROWS, NCOLS)
        return arr.T

    def updatemap(self, ghosts):
        self.curmap = self.basemap.copy()
        for i in ghosts:
            if not i.mode.current == FREIGHT:
                x1 = math.floor(i.position.x / TILEWIDTH)
                x2 = math.ceil(i.position.x / TILEWIDTH)
                y1 = math.floor(i.position.y / TILEHEIGHT)
                y2 = math.ceil(i.position.y / TILEHEIGHT)
                self.curmap[x1][y1] = 2
                self.curmap[x2][y1] = 2
                self.curmap[x1][y2] = 2
                self.curmap[x2][y2] = 2
                
                self.curmap[(x1-1)%28][y1] = 2
                self.curmap[(x2+1)%28][y1] = 2
                self.curmap[(x1-1)%28][y2] = 2
                self.curmap[(x2+1)%28][y2] = 2
                
                self.curmap[x1][(y1-1)%36] = 2
                self.curmap[x2][(y1-1)%36] = 2
                self.curmap[x1][(y2+1)%36] = 2
                self.curmap[x2][(y2+1)%36] = 2

    def trace(self, celldetail, target):
        x = target.x
        y = target.y
        direction = None
        
        while (celldetail[x][y].parent_x != x or celldetail[x][y].parent_y != y):
            if (x > celldetail[x][y].parent_x):
                direction = RIGHT
            if (x < celldetail[x][y].parent_x):
                direction = LEFT
            if (y > celldetail[x][y].parent_y):
                direction = DOWN
            if (y < celldetail[x][y].parent_y):
                direction = UP
            x = celldetail[x][y].parent_x
            y = celldetail[x][y].parent_y
        
        return direction
        
    def a_star(self, target):
        curcell_x = round(self.position.x / TILEWIDTH)  #x (0, 28)
        curcell_y = round(self.position.y / TILEHEIGHT) #y (0, 36)
        
        if curcell_x == target.x and curcell_y == target.y:
            self.target_set = False
            return
        
        if (    (self.direction ==  1 and self.curmap[curcell_x][curcell_y-1] == 2) 
            or  (self.direction == -1 and self.curmap[curcell_x][curcell_y+1] == 2)  ):
            if (self.curmap[curcell_x-1][curcell_y] == 0): return 2
            if (self.curmap[curcell_x+1][curcell_y] == 0): return -2
            return -self.direction
        if (    (self.direction ==  2 and self.curmap[curcell_x-1][curcell_y] == 2)
            or  (self.direction == -2 and self.curmap[curcell_x+1][curcell_y] == 2)  ):
            if (self.curmap[curcell_x][curcell_y-1] == 0): return 1
            if (self.curmap[curcell_x][curcell_y+1] == 0): return -1
            return -self.direction
        
        if self.curmap[target.x][target.y] == 2:
            self.target_able = False
            return
        
        closeList = np.random.choice([False], p=[1], size = NROWS*NCOLS)
        closeList = closeList.reshape(NCOLS, NROWS)
        
        list = []
        for i in range(NROWS*NCOLS):
            c = cell()
            list.append(c)
        
        arr = np.array(list)
        celldetail = arr.reshape(NCOLS, NROWS)
        
        celldetail[curcell_x][curcell_y].f = 0
        celldetail[curcell_x][curcell_y].g = 0
        celldetail[curcell_x][curcell_y].h = 0
        celldetail[curcell_x][curcell_y].parent_x = curcell_x
        celldetail[curcell_x][curcell_y].parent_y = curcell_y
        
        openList = []
        openList.append([0, curcell_x, curcell_y])
        
        while (openList.__len__() != 0):
            openList.sort()
            p = openList[0]
            openList.pop(0)
            x = p[1]
            y = p[2]
            closeList[x, y] = True
            
            #Leftcell
            if (x - 1 >= 0):
                if (x - 1 == target.x and y == target.y):
                    celldetail[x - 1][y].parent_x = x
                    celldetail[x - 1][y].parent_y = y
                    return self.trace(celldetail, target)
                
                elif (closeList[x - 1][y] == False and self.curmap[x - 1][y] == 0):
                    gnew = celldetail[x][y].g + 1
                    hnew = abs(x - 1 - target.x) + abs(y - target.y)
                    fnew = gnew + hnew
                    if (celldetail[x - 1][y].f > fnew):
                        openList.append([fnew, x - 1, y])
                        celldetail[x - 1][y].f = fnew
                        celldetail[x - 1][y].g = gnew
                        celldetail[x - 1][y].h = hnew
                        celldetail[x - 1][y].parent_x = x
                        celldetail[x - 1][y].parent_y = y
                        
            #Rightcell
            if (x + 1 < NCOLS):
                if (x + 1 == target.x and y == target.y):
                    celldetail[x + 1][y].parent_x = x
                    celldetail[x + 1][y].parent_y = y
                    return self.trace(celldetail, target)
                
                elif (closeList[x + 1][y] == False and self.curmap[x + 1][y] == 0):
                    gnew = celldetail[x][y].g + 1
                    hnew = abs(x + 1 - target.x) + abs(y - target.y)
                    fnew = gnew + hnew
                    if (celldetail[x + 1][y].f > fnew):
                        openList.append([fnew, x + 1, y])
                        celldetail[x + 1][y].f = fnew
                        celldetail[x + 1][y].g = gnew
                        celldetail[x + 1][y].h = hnew
                        celldetail[x + 1][y].parent_x = x
                        celldetail[x + 1][y].parent_y = y
            
            #Upcell            
            if (y - 1 >= 0):
                if (x == target.x and y - 1 == target.y):
                    celldetail[x][y - 1].parent_x = x
                    celldetail[x][y - 1].parent_y = y
                    return self.trace(celldetail, target)
                
                elif (closeList[x][y - 1] == False and self.curmap[x][y - 1] == 0):
                    gnew = celldetail[x][y].g + 1
                    hnew = abs(x - target.x) + abs(y - 1 - target.y)
                    fnew = gnew + hnew
                    if (celldetail[x][y - 1].f > fnew):
                        openList.append([fnew, x, y - 1])
                        celldetail[x][y - 1].f = fnew
                        celldetail[x][y - 1].g = gnew
                        celldetail[x][y - 1].h = hnew
                        celldetail[x][y - 1].parent_x = x
                        celldetail[x][y - 1].parent_y = y
                    
            #Downcell
            if (y + 1 < NROWS):
                if (x == target.x and y + 1 == target.y):
                    celldetail[x][y + 1].parent_x = x
                    celldetail[x][y + 1].parent_y = y
                    return self.trace(celldetail, target)
                
                elif (closeList[x][y + 1] == False and self.curmap[x][y + 1] == 0):
                    gnew = celldetail[x][y].g + 1
                    hnew = abs(x - target.x) + abs(y + 1 - target.y)
                    fnew = gnew + hnew
                    if (celldetail[x][y + 1].f > fnew):
                        openList.append([fnew, x, y + 1])
                        celldetail[x][y + 1].f = fnew
                        celldetail[x][y + 1].g = gnew
                        celldetail[x][y + 1].h = hnew
                        celldetail[x][y + 1].parent_x = x
                        celldetail[x][y + 1].parent_y = y
                        
    def TwoPointDis(self, posA, posB):
        x1 = posA.x
        y1 = posA.y
        x2 = posB.x
        y2 = posB.y
        d1 = x1 - x2 
        d2 = y1 - y2
        return d1**2 + d2**2

    def sqrtEucDis(self, temp):
        return math.sqrt(temp)
    
    
class cell:  
    def __init__(self):
        self.parent_x = -1
        self.parent_y = -1
        self.f = np.inf
        self.g = np.inf
        self.h = np.inf