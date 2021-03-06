#!/usr/bin/env python3
# Nicolas Seriot
# 2021-10-03
# Basic terrain editor to discover PyGame.

import pygame
import sys

BLUE = (0,0,255)
GREEN = (0,255,0)

IMG_FOREST = pygame.image.load("tiles/forest.png")
IMG_FOREST_ = pygame.image.load("tiles/forest_s.png")
IMG_TERRAIN = pygame.image.load("tiles/terrain.png")
IMG_TERRAIN_ = pygame.image.load("tiles/terrain_s.png")
IMG_BUILDING = pygame.image.load("tiles/building.png")
IMG_BUILDING_ = pygame.image.load("tiles/building_s.png")

class Block(pygame.sprite.DirtySprite):

    def __init__(self, x, y, v):
        pygame.sprite.DirtySprite.__init__(self)

        self.cell_x = x
        self.cell_y = y
        self._value = v

        self.image_wall = IMG_FOREST
        self.image_wall_ = IMG_FOREST_

        self.image_terrain = IMG_TERRAIN
        self.image_terrain_ = IMG_TERRAIN_
                
        self.image_building = IMG_BUILDING
        self.image_building_ = IMG_BUILDING_

        self._is_highlighted = False

        self.update()
        self.rect = self.image.get_rect()
        
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, b: bool):
        if b != self._value:
            self._value = b 
            self.dirty = 1

    @property
    def is_highlighted(self):
        return self._is_highlighted
    
    @is_highlighted.setter
    def is_highlighted(self, b: bool):
        if b != self._is_highlighted:
            self._is_highlighted = b 
            self.dirty = 1

    def __str__ (self):
        return 'Block(cell_x=' + str(self.cell_x) + ' , cell_y=' + str(self.cell_y) + ')'
        
    def hit(self):
        print("hit", self.cell_x, self.cell_y)
    
    def update(self):
        # prepare to draw


        if self.dirty == 0:
            return

        print("--", self, ".update()")

        if self.value == 2:
            self.image_standard = self.image_building
            self.image_highlighted = self.image_building_
        elif self.value == 1:
            self.image_standard = self.image_wall
            self.image_highlighted = self.image_wall_
        else:
            self.image_standard = self.image_terrain
            self.image_highlighted = self.image_terrain_

        self.image = self.image_highlighted if self._is_highlighted else self.image_standard
        self.mask = pygame.mask.from_surface(self.image)

        self.dirty = 1

class World(object):

    def __init__(self):
        super().__init__()

        self.model = [
        [2, 0, 1, 1, 1, 0],
        [1, 1, 1, 1, 2, 1],
        [1, 1, 2, 1, 1, 0],
        [1, 0, 0, 0, 1, 0],
        [1, 1, 1, 1, 2, 1]
        ]

        self.X = len(self.model)
        self.Y = len(self.model[0])

        self.font = pygame.font.SysFont('Courier New', 24, True, False)
        self.text_is_dirty = 1

        self.m = []
        for x in range(self.X):
            l = []
            for y in range(self.Y):
                l.append(None)
            self.m.append(l)

        self.selected_block: Block = None
        self.tool_value = 0

        self.info_sprite = pygame.sprite.Sprite()
        self.info_sprite.rect = pygame.Rect(50,50,50,50)

        self.create_tools()

        self.create_blocks()

        self.label_1 = Label(txt="", location=(50,300), size=(600,40), font=self.font)
        self.label_2 = Label(txt="", location=(50,330), size=(600,40), font=self.font)
        self.label_3 = Label(txt="", location=(50,360), size=(600,40), font=self.font)

    def nb_buildings(self):
        count = 0
        for l in self.m:
            for b in l:
                if b.value == 2:
                    count += 1
        return count

    def set_selection(self, b: Block):
        if b == None:
            # TODO: unselect everything
            return False

        #print("-- CHANGE SELECTION FROM", before_x, before_y, "TO", b.cell_x, b.cell_y)

        if b == self.selected_block:
            return False

        if self.selected_block:
            self.selected_block.is_highlighted = False
        self.selected_block = b
        self.selected_block.is_highlighted = True

        self.text_is_dirty = 1
        #print("-- selection is now", b.cell_x, b.cell_y)

        return True
    
    def create_blocks(self):

        #self.blocks = pygame.sprite.LayeredDirty()

        TW, TH = 64, 64
        TW2, TH2 = TW/2, TH/2
    
        l = []

        # start adding from the back
        for x in range(self.X)[::-1]:
            for y in range(self.Y)[::-1]:
                v = self.model[x][y]

                b = Block(x,y,v)
                                
                cart_x = x * TW2
                cart_y = y * TH2

                iso_x = (cart_x - cart_y) 
                iso_y = (cart_x + cart_y)/2

                b.rect.x = self.X*TH2/2 + iso_x + 200
                b.rect.y = self.Y*TH2 - iso_y

                self.m[x][y] = b

                #print("SET", x, y, "->", b)

                l.append(b)
        
        t = tuple(l)
        self.blocks = pygame.sprite.LayeredDirty(t)

    def create_tools(self):

        self.tools = pygame.sprite.Group()

        b0 = Block(0, 0, 0)
        b0.rect = pygame.Rect(10, 10, 64, 64)    
        b1 = Block(0, 0, 1)
        b1.rect = pygame.Rect(10, 90, 64, 64)    
        b2 = Block(0, 0, 2)
        b2.rect = pygame.Rect(10, 170, 64, 64)

        self.tools.add(b0)
        self.tools.add(b1)
        self.tools.add(b2)

    def build_on_selection(self):
        b = self.selected_block

        if not b:
            return
        
        b.value = self.tool_value

        self.text_is_dirty = 1

    def sprite_for_pos(self, pos):

        for s in list(self.blocks)[::-1]: #type: Block
            if s.rect.collidepoint(pos):
                pos_in_mask = pos[0] - s.rect.x, pos[1] - s.rect.y
                if s.mask.get_at(pos_in_mask):
                    return s
        return None
    
    def update_tools_with_hit(self, pos):

        for b in self.tools:
            if b.rect.collidepoint(pos):
                print("-- set tool value", b.value)
                self.tool_value = b.value
                return True
        
        return False

    def select_neighbour(self, x_offset, y_offset):

        current_selection = self.selected_block

        x,y = 0,0

        if current_selection:
            x = current_selection.cell_x
            y = current_selection.cell_y

        x_ = x + x_offset
        y_ = y + y_offset

        if not x_ in range(self.X) or not y_ in range(self.Y):
            print("OUT OF RANGE", x_, y_)
            return None

        b = self.m[x_][y_]
        self.set_selection(b)
        return b
    
    def draw(self, screen):
        print("-- draw")

        self.blocks.update()
        rects = self.blocks.draw(screen)
        pygame.display.update(rects)

        if self.text_is_dirty == 1:
            sb = self.selected_block
            self.label_1.txt = "No selection" if not sb else "Selected: %d,%d" % (sb.cell_x, sb.cell_y)
            self.label_1.update()
            screen.blit(self.label_1.surface, self.label_1.location)

            self.label_2.txt = "Buildings: %d" % self.nb_buildings()
            self.label_2.update()
            screen.blit(self.label_2.surface, self.label_2.location)

            self.label_3.txt = "Use mouse, or arrows and space bar"
            self.label_3.update()
            screen.blit(self.label_3.surface, self.label_3.location)

            self.text_is_dirty = 0

        for t in self.tools:
            t.is_highlighted = t.value == self.tool_value

        self.tools.update()
        rects = self.tools.draw(screen)
        pygame.display.update(rects)
        
        pygame.display.flip()

class Label():

    def __init__(self, txt, location, size, font, bg=BLUE, fg=GREEN):
        self.bg = bg  
        self.fg = fg
        self.size = size
        self.font = font
        self.location = location

        self.font = font
        self.txt = txt
        self.txt_surf = self.font.render(self.txt, 1, self.fg)
        #self.txt_rect = self.txt_surf.get_rect(center=[s/2 for s in self.size])

        self.surface = pygame.surface.Surface(size)
        self.rect = self.surface.get_rect(topleft=location) 

    def update(self):
        self.surface.fill(self.bg)
        self.txt_surf = self.font.render(self.txt, 1, self.fg)
        self.surface.blit(self.txt_surf, (0,0))

def main():
    pygame.init()
    
    window_size = (640, 480)
    screen = pygame.display.set_mode(window_size)

    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill(BLUE)

    pygame.display.set_caption("Basic Terrain Editor")

    clock = pygame.time.Clock()

    w = World()
    w.blocks.clear(screen, background)

    w.draw(screen)

    while True:
        
        clock.tick(30)

        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                print("-- key", event.key)

                if event.key == pygame.K_LEFT:
                    print("    left")
                    w.select_neighbour(-1,0)
                    w.draw(screen)
                elif event.key == pygame.K_RIGHT:
                    print("    right")
                    w.select_neighbour(1,0)
                    w.draw(screen)
                elif event.key == pygame.K_UP:
                    print("    up")
                    w.select_neighbour(0,1)
                    w.draw(screen)
                elif event.key == pygame.K_DOWN:
                    print("    down")
                    w.select_neighbour(0,-1)
                    w.draw(screen)
                elif event.key == pygame.K_PAGEUP:
                    print("    page up")
                elif event.key == pygame.K_PAGEDOWN:
                    print("    page down")
                elif event.key == pygame.K_SPACE:
                    print("-- space")
                    b = w.selected_block
                    if b:
                        b.value = w.tool_value
                        w.draw(screen)
                elif event.key == 115: # s
                    print("-- screenshot")
                    pygame.image.save(screen, "screenshot.png")
                elif event.key == 113: # q
                    print("-- quit")
                    pygame.quit()
                    sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                print("-", event.button)

                pressed1, pressed2, pressed3 = pygame.mouse.get_pressed()                
                if not pressed1:
                    break

                pos = pygame.mouse.get_pos()

                s = w.sprite_for_pos(pos)
                if s:
                    w.set_selection(s)
                    s.value = w.tool_value
                    w.text_is_dirty = 1
                    w.draw(screen)
                else:
                    tool_has_changed = w.update_tools_with_hit(pos)
                    if tool_has_changed:
                        w.text_is_dirty = 1
                        w.draw(screen)
            
            elif event.type == pygame.MOUSEMOTION:
                pos = pygame.mouse.get_pos()

                s = w.sprite_for_pos(pos)
                if not s:
                    break
                
                must_draw = False

                selection_has_changed = w.set_selection(s)

                pressed1, pressed2, pressed3 = pygame.mouse.get_pressed()                
                if pressed1:
                    if s.value != w.tool_value:
                        must_draw = True
                        s.value = w.tool_value
                
                if selection_has_changed:
                    must_draw = True

                if must_draw:
                    w.draw(screen)            

if __name__ == "__main__":
    
    main()
