import pygame
import neat
import time
import os
import random
pygame.font.init()

WIDTH = 500
HEIGHT = 800

BIRD_IMAGE = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]

PIPE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

ACCELERATION = 3
BG_VEL = 10
TERMINAL_VELOCITY = 16
JUMP_FORCE = -10.5

STAT_FONT = pygame.font.SysFont("comicsans", 50)

class Bird: 
    IMGS = BIRD_IMAGE
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = y
        self.img_count = 0
        self.img = self.IMGS[0]
    
    def jump(self):
        #Top left is 0,0 --> to go up you have to go smaller number
        self.vel = JUMP_FORCE
        
        #Reset jump time
        self.tick_count = 0

        self.height = self.y

    #Natural movement based on gravity
    def move(self):
        #Represents time
        self.tick_count += 1
        
        # x = v0 * t + 0.5 * a * t^2
        #Showing displacement
        d = self.vel * self.tick_count + ACCELERATION/2 * self.tick_count**2
        #self.vel = self.vel + ACCELERATION * self.tick_count

        #terminal velocity
        if d >= TERMINAL_VELOCITY: 
            d = TERMINAL_VELOCITY
        
        #higher or lower jump
        if d < 0:
            d -= 2
        
        #Changing bird height by d
        self.y += d

        #tilt bird if going up
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        #tilt bird if going down
        else: 
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, window):
        #how much time a img has been shown
        self.img_count += 1

        #What image should be shown based on img_count
        #image changes every 5 ticks 
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        #if bird is tilting down (falling), it shouldn't flap
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        #Image is rotated, but will rotate at (0,0) of .png
        #We want the rotation on the birds center
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center)
        
        #Draw the bird on the window
        window.blit(rotated_image, new_rect.topleft)

    #gets mask of bird for collision detection
    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200
    VEL = BG_VEL

    def __init__(self, x):
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0

        #Make pipe facing up and down
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMAGE, False, True)
        self.PIPE_BOTTOM = PIPE_IMAGE

        #has bird passed the pipe
        self.passed = False
        self.set_height()

    def set_height(self):
        #getting random height at which pipe gap will be at
        self.height = random.randrange(50, 450)

        #getting location where to draw top pipe
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    #moving pipe to the left to think of movement
    def move(self):
        self.x -= self.VEL

    def draw(self, window):
        window.blit(self.PIPE_TOP, (self.x, self.top))
        window.blit(self.PIPE_BOTTOM, (self.x, self.bottom))
    
    #pass true for collide, false for no
    def collide(self, bird):
        bird_mask = bird.get_mask()

        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        #Calculating how far the masks are away from each other
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        #Returns collision piont, if no collision --> return None
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        #Return whether collision happens
        if t_point or b_point:
            return True
        
        return False

class Base: 
    VEL = BG_VEL
    WIDTH = BASE_IMAGE.get_width()

    def __init__(self,y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    #Drawing two images so that we can have a continuous background
    def move(self):
        #moving both images to the left
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        #moving images once it finishes scrolling 
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, window):
        window.blit(BASE_IMAGE, (self.x1, self.y))
        window.blit(BASE_IMAGE, (self.x2, self.y))
        
#Draws Background and bird
def draw_window(window, birds, pipes, base, score):
    window.blit(BG_IMAGE, (0,0))
    for pipe in pipes:
        pipe.draw(window)
    base.draw(window)

    for bird in birds:
        bird.draw(window)
    

    text = STAT_FONT.render("Score: " + str(score), 1, (255,255,255))
    window.blit(text, (WIDTH - 10 - text.get_width(), 10))

    pygame.display.update()

#Main Method + Fitness Function
def main(genomes, config):

    nets = []
    ge = []
    birds = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)

    base = Base(y = 730)
    pipes = [Pipe(600)]
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    score = 0
    run = True

    while run:
        #forces while loop to slow down, and run 30 times per second
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        #Gets the next pipe index and checks if birds are left
        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break
        

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.03

            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
            if output[0] > 0.5:
                bird.jump()

        add_pipe = False
        removedPipes = []

        if pygame.mouse.get_pressed()[0]:
            bird.jump()

        for pipe in pipes:
            for x, bird in enumerate(birds): 
                #checks collision
                if pipe.collide(bird):
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)
                
                #Checking if pipe was passed
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            #Once pipe has cleared the screen, pipe should be removed
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                removedPipes.append(pipe)

            pipe.move()
            
        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 2
            pipes.append(Pipe(600))

        for r in removedPipes:
            pipes.remove(r)

        for x, bird in enumerate(birds): 
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0: 
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)
        
        base.move()

        if score > 50:
            break

        draw_window(window, birds, pipes, base, score)       
    
def run(configPath):
    config = neat.config.Config(neat.DefaultGenome, 
                neat.DefaultReproduction, 
                neat.DefaultSpeciesSet, 
                neat.DefaultStagnation, configPath)

    pop = neat.Population(config)

    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)

    winner = pop.run(main, 50)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    configPath = os.path.join(local_dir, "NEAT_Config.txt")
    run(configPath)