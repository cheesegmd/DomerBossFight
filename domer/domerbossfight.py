import pygame, random, time, numpy

width, height = 1000, 700
FPS = 60
playersize = 35, 35
COLORS = [
    (0, 0, 0), # black
    (255, 255, 255), # white
    (125, 60, 255), # player
    (50, 50, 50), # grid
    (255, 100, 100), # domer (projectile)
    (255, 0, 0), # domer's projectile
]
CELL_SIZE = 20

GRID_ROWS = width // CELL_SIZE
GRID_COLS = height // CELL_SIZE

debug = False

defpath = R"C:\Users\CAMERON\Documents\python\desktop clutterer"

# grid array
grid_data = numpy.zeros((height, width, 3), dtype=numpy.uint8)
grid_data[:, :] = COLORS[0]

# horizontal grid lines
for y in range(0, height, CELL_SIZE):
    grid_data[y, :, :] = COLORS[3]

# vertical grid lines
for x in range(0, width, CELL_SIZE):
    grid_data[:, x, :] = COLORS[3]

# more lines
if height % CELL_SIZE != 0:
    grid_data[height - 1, :, :] = COLORS[3]

if width % CELL_SIZE != 0:
    grid_data[:, width - 1, :] = COLORS[3]

grid_surface = pygame.surfarray.make_surface(numpy.transpose(grid_data, (1, 0, 2)))

pygame.mixer.pre_init(44100, -16, 2, 512) # frequency, size, channels, buffer
pygame.init()
fade_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
ALPHA = 36 # fade amount per frame
domer_image1_path = Rf"{defpath}\domer\domerassets\phases\domer_phase1.png"

pygame.mixer.init()
try:
    domer1_sfx = pygame.mixer.Sound(Rf"{defpath}\domer\domerassets\audio\sfx\domer1.mp3")
    domer1_sfx.set_volume(0.3)
    ding_sfx = pygame.mixer.Sound(Rf"{defpath}\domer\domerassets\audio\sfx\ding.mp3")
    ding_sfx.set_volume(0.15)
    hurt_sfx = pygame.mixer.Sound(Rf"{defpath}\domer\domerassets\audio\sfx\projectile.mp3")
    hurt_sfx.set_volume(0.2)
except pygame.error as e:
    print(f"Could not load a sound file.")
    pygame.quit()
    exit()
pygame.mixer.music.load(Rf"{defpath}\domer\domerassets\audio\music\Scourge of the universe 4.mp3")
pygame.mixer.music.set_volume(0.02)

pygame.font.init()
font_path = Rf"{defpath}\domer\domerassets\cascadiacode\ttf\CascadiaCodePLItalic.ttf"
font_size = 40
try:
    cascadia_font = pygame.font.Font(font_path, font_size)
    boss_font = pygame.font.Font(font_path, 20)
    health_font = pygame.font.Font(font_path, 14)
except FileNotFoundError:
    print(f"Error: Font file not found at {font_path}. Please check the path.")
    pygame.quit()
    exit()

screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("defeat the domers.")
running = True

clock = pygame.time.Clock()
UPDATE_COUNTER_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(UPDATE_COUNTER_EVENT, 1000)

text_surface = cascadia_font.render(str(round(clock.get_fps())) + " FPS", True, (255, 255, 255, 100)) # White text

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, projectile_group):
        super().__init__()

        # surface of player
        self.image = pygame.Surface(playersize)
        self.image.fill(COLORS[2])

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        self.speed = 4
        self.truex = self.rect.x
        self.truey = self.rect.y

        # aim vector
        self.aim_x = 0
        self.aim_y = 0

        # external reference to projectile group
        self.projectiles = projectile_group

        # shoot cooldown (frames)
        self.shoot_cooldown = 10

        self.health = 30.0

    def handle_input(self, keys_pressed):
        desvelx = 0
        desvely = 0

        # WASD movement
        if keys_pressed[pygame.K_a]:
            desvelx -= 1
        if keys_pressed[pygame.K_d]:
            desvelx += 1
        if keys_pressed[pygame.K_w]:
            desvely -= 1
        if keys_pressed[pygame.K_s]:
            desvely += 1

        movement_vector = numpy.array([desvelx, desvely], dtype=float)
        magnitude = numpy.linalg.norm(movement_vector)

        if magnitude > 0:
            movement_vector = movement_vector / magnitude
            self.truex += movement_vector[0] * self.speed
            self.truey += movement_vector[1] * self.speed

        # clamp to screen
        self.rect.x = self.truex
        self.rect.y = self.truey
        if self.rect.left < 0:   self.rect.left = 0;   self.truex = self.rect.x
        if self.rect.right > width: self.rect.right = width; self.truex = self.rect.x
        if self.rect.top < 0:    self.rect.top = 0;    self.truey = self.rect.y
        if self.rect.bottom > height: self.rect.bottom = height; self.truey = self.rect.y

        # Arrow key aiming
        self.aim_x = keys_pressed[pygame.K_RIGHT] - keys_pressed[pygame.K_LEFT]
        self.aim_y = keys_pressed[pygame.K_DOWN] - keys_pressed[pygame.K_UP]

    def try_shoot(self, keys_pressed):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            return

        if self.aim_x != 0 or self.aim_y != 0:
            # normalize aim vector
            mag = (self.aim_x ** 2 + self.aim_y ** 2) ** 0.5
            vx = self.aim_x / mag
            vy = self.aim_y / mag
            # spawn projectile
            self.projectiles.add(Projectile(self.rect.centerx, self.rect.centery, vx, vy, damage=1))
            self.shoot_cooldown = 10  # in frames

    def update(self, keys_pressed):
        self.handle_input(keys_pressed)
        self.try_shoot(keys_pressed)


class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, velx, vely, damage=1):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill(COLORS[4])
        self.rect = self.image.get_rect(center=(x, y))
        self.velx = velx
        self.vely = vely
        self.speed = 6
        self.damage = damage

    def update(self):
        self.rect.x += self.velx * self.speed
        self.rect.y += self.vely * self.speed

        if (self.rect.right < 0 or self.rect.left > width or
            self.rect.bottom < 0 or self.rect.top > height):
            self.kill()

class BossProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, velx, vely, color=(255,0,0), size=10, bounce=True, decay=300, damage=1, attype="none"):
        super().__init__()
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.truex = float(x)
        self.truey = float(y)
        self.velx = velx
        self.vely = vely
        self.bounce = bounce
        self.decaytimer = decay
        self.size = size
        self.damage = damage

        # play firing sound (none exist yet)

        if attype == "normal":
            return None
        if attype == "special":
            return None

    def update(self):
        self.truex += self.velx
        self.truey += self.vely

        self.rect.x = self.truex
        self.rect.y = self.truey

        if self.bounce:
            if self.rect.left < 0 - self.size or self.rect.right > width + self.size:
                self.velx *= -1
            if self.rect.top < 0 - self.size or self.rect.bottom > height + self.size:
                self.vely *= -1


        self.decaytimer -= 1
        if self.decaytimer <= 0:
            self.kill()


class Domer(pygame.sprite.Sprite):
    def __init__(self, x, y, boss_projectile_group):
        super().__init__()
        self.image = pygame.image.load(domer_image1_path).convert_alpha() # Load image with transparency
        self.rect = self.image.get_rect(center=(x, y))

        self.health = 300
        self.max_health = 300

        self.speedx = 1
        self.speedy = -1

        self.projectiles = boss_projectile_group
        self.shoot_cooldown = 100  # frames
        self.intro_timer = 150
        self.attack_cooldown = 180

    def update(self):
        if self.intro_timer < 0 :
            # there is motion detected at your front door
            self.rect.x += self.speedx
            self.rect.y += self.speedy
            # bounce off edges
            if self.rect.left < 0 or self.rect.right > width:
                self.speedx *= -1
            if self.rect.top < 0 or self.rect.bottom > height:
                self.speedy *= -1

            # shooting
            if self.shoot_cooldown > 0:
                self.shoot_cooldown -= 1
            else:
                self.shoot("normal", type="normal")
                self.shoot_cooldown = 15

            if self.attack_cooldown <= 0:
                # special attack 50% of the time
                if random.random() < 0.5:
                    self.special_attack()
               
                self.attack_cooldown = 180  # reset cooldown   
            self.attack_cooldown -= 1

        else:
            self.intro_timer -= 1
        
        if self.intro_timer == 60 :
            domer1_sfx.play()
        if self.intro_timer == 0 :
            ding_sfx.play()
            pygame.mixer.music.play()

    def shoot(self, choice, type):
        if not choice:
            choice = random.choice(["normal", "fast", "slow"])
        
        if choice == "normal":
            # normal bouncing projectile
            self.projectiles.add(BossProjectile(
                self.rect.centerx, self.rect.centery,
                random.uniform(-4.0,4.0), random.uniform(-4.0,4.0), damage=1, attype=type
            ))
        elif choice == "fast":
            # fast small projectile that doesn't bounce
            self.projectiles.add(BossProjectile(
                self.rect.centerx, self.rect.centery,
                random.uniform(-8.0,8.0), random.uniform(-8.0,8.0),
                color=(0,0,255), size=5, bounce=True, decay=120, damage=0.5, attype=type
            ))
        elif choice == "slow":
            # fast small projectile that doesn't bounce
            self.projectiles.add(BossProjectile(
                self.rect.centerx, self.rect.centery,
                random.uniform(-3.0,3.0), random.uniform(-3.0,3.0),
                color=(0,50,150), size=16, bounce=False, decay=600, damage=2, attype=type
            ))
        elif choice == "checkmark":
            # fast projectile that doesn't bounce, starts by facing player direction, backing up, and then accelerating.
            self.projectiles.add(BossProjectile(
                self.rect.centerx, self.rect.centery,
                random.randint(-8.0,8.0), random.randint(-8.0,8.0),
                color=(0,0,255), size=8, bounce=False, decay=120, damage=2
            ))


    def special_attack(self):
        attack = random.randint(0, 1)
        if attack == 0:
            for angle in range(0, 360, 12):
                rad = numpy.radians(angle)
                self.projectiles.add(BossProjectile(
                self.rect.centerx, self.rect.centery,
                5 * numpy.cos(rad), 5 * numpy.sin(rad),
                color=(255,0,255), size=8, bounce=False, attype="ring"))
        elif attack == 1:
            a = 0
            while a < 20:
                self.shoot(random.choice(["normal", "fast", "slow"]), type="special")
                a+=1

all_sprites = pygame.sprite.Group()
projectiles = pygame.sprite.Group()
bossgroup = pygame.sprite.Group()
player = Player(width // 2, height - 50, projectiles)  
all_sprites.add(player)

boss_projectiles = pygame.sprite.Group()

boss = Domer(width // 2, 100, boss_projectiles)

bossgroup.add(boss)

grid_offset_x = 0.0
grid_offset_y = 0.0

grid_scroll_speed_x = 1   # floats work, but flicker
grid_scroll_speed_y = -0.5 

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == UPDATE_COUNTER_EVENT:
            text_surface = cascadia_font.render(
                str(round(clock.get_fps())) + " FPS", True, (255,255,255)
            )

    keys = pygame.key.get_pressed()
    player.update(keys)
    projectiles.update()
    boss.update()
    boss_projectiles.update()

    # boss hit by player bullet
    hits = pygame.sprite.spritecollide(boss, projectiles, True)
    for bullet in hits:
        boss.health -= bullet.damage

    hits = pygame.sprite.spritecollide(player, boss_projectiles, True)
    for bullet in hits:
        player.health -= bullet.damage
        hurt_sfx.play()
        if player.health <= 0:
            running = False


    plrxtext = cascadia_font.render(str(round(player.truex, 2)), True, (0, 0, 255))
    plrytext = cascadia_font.render(str(round(player.truey, 2)), True, (255, 0, 0))
    bosshealth = boss_font.render(str(round(boss.health)), True, (150, 0, 0))
    healthcounter = health_font.render(str(round(player.health, 2)), True, (70, 30, 100))


    grid_offset_x = (grid_offset_x + grid_scroll_speed_x) % CELL_SIZE
    grid_offset_y = (grid_offset_y + grid_scroll_speed_y) % CELL_SIZE
    src_x = int(grid_offset_x)
    src_y = int(grid_offset_y)

    src_rect = pygame.Rect(src_x, src_y, width, height)
    grid_surface.set_alpha(80)

    screen.blit(grid_surface, (0, 0), src_rect)

    # wrap X
    if src_x + width > grid_surface.get_width():
        wrap_x = grid_surface.get_width() - src_x
        screen.blit(grid_surface, (wrap_x, 0),
                    pygame.Rect(0, src_y, width - wrap_x, height))

    # wrap Y
    if src_y + height > grid_surface.get_height():
        wrap_y = grid_surface.get_height() - src_y
        screen.blit(grid_surface, (0, wrap_y),
                    pygame.Rect(src_x, 0, width, height - wrap_y))

    # wrap both
    if (src_x + width > grid_surface.get_width()
        and src_y + height > grid_surface.get_height()):

        screen.blit(grid_surface, (wrap_x, wrap_y),
                    pygame.Rect(0, 0, width - wrap_x, height - wrap_y))


    projectiles.draw(screen)
    boss_projectiles.draw(screen)
    all_sprites.draw(screen)
    bossgroup.draw(screen)

    # Domer healthbar
    pygame.draw.rect(screen, (150,50,50), (20, 20, width-40, 20))  # background
    pygame.draw.rect(screen, (255,0,0), (20, 20, (width-40) * (boss.health / boss.max_health), 20))

    screen.blit(bosshealth, (20, 18))
    screen.blit(healthcounter, (player.rect.x, player.rect.y+(playersize[0]/2)-8))
    if debug:   
        screen.blit(text_surface, (0, 0))
        screen.blit(plrxtext, (player.rect.x+60, player.rect.y-20))
        screen.blit(plrytext, (player.rect.x+60, player.rect.y+10))

    pygame.display.flip()
    clock.tick(FPS)
