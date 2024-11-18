import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Shooter Game")

# Colors
canvasGRAY = (215, 215, 215)
enemyBLUE = (50, 183, 240)
enemyFrozenBLUE = (116, 146, 157)
bossORANGE = (255, 97, 42)
bulletGREEN = (2, 255, 7)
healthYELLOW = (255, 255, 5)
textWHITE = (255, 255, 255)
playerBLUE = (2, 255, 255)

# Clock and font
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 55)

# Player settings
player_img = pygame.Surface((35, 35))
player_img.fill(playerBLUE)
player_x = SCREEN_WIDTH // 2 - 25
player_y = SCREEN_HEIGHT - 70
player_speed = 7
player_lives = 3

# Bullet settings
bullet_img = pygame.Surface((10, 30))
bullet_img.fill(bulletGREEN)
bullet_speed = -20
bullet_state = "ready"
bullet_x = 0
bullet_y = player_y

# Enemy settings
Enemy_COUNT = 10
enemy_list = []
enemy_img = pygame.Surface((35, 35))
for i in range(Enemy_COUNT):
    Enemy_speed = random.choice([3, 4, 5])
    Enemy_x_location = random.randint(0, SCREEN_WIDTH - 50)
    Enemy_y_location = random.randint(50, 300)
    enemy_list.append([Enemy_x_location, Enemy_y_location, Enemy_speed, enemyBLUE])

# Boss settings
boss_img = pygame.Surface((50, 50))
boss_img.fill(bossORANGE)
boss_x = SCREEN_WIDTH - 100
boss_y = 50
boss_speed = -5
boss_active = True

# Game state
score = 0
time_remaining = 60
game_state = "playable"


def display_text(text, x, y):
    screen_text = font.render(text, True, textWHITE)
    SCREEN.blit(screen_text, [x, y])


def reset_game():
    global player_lives, bullet_state, bullet_x, bullet_y, boss_active, boss_x, game_state, score, time_remaining
    player_lives = 3
    bullet_state = "ready"
    bullet_x = 0
    bullet_y = player_y
    enemy_list.clear()
    for _ in range(Enemy_COUNT):
        Enemy_speed = random.choice([3, 4, 5])
        Enemy_x_location = random.randint(0, SCREEN_WIDTH - 50)
        Enemy_y_location = random.randint(50, 300)
        enemy_list.append([Enemy_x_location, Enemy_y_location, Enemy_speed, enemyBLUE])
    boss_active = True
    boss_x = SCREEN_WIDTH - 100
    game_state = "playable"
    score = 0
    time_remaining = 60


last_time = pygame.time.get_ticks()

# Main game loop
while True:
    SCREEN.fill(canvasGRAY)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and bullet_state == "ready":
                bullet_x = player_x + 20
                bullet_state = "fired"
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

    # Player movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and player_x > 0:
        player_x -= player_speed
    if keys[pygame.K_RIGHT] and player_x < SCREEN_WIDTH - 50:
        player_x += player_speed
    print(player_x, player_y)

    # Bullet movement
    if bullet_state == "fired":
        bullet_y += bullet_speed
        if bullet_y < 0:
            bullet_state = "ready"
            bullet_y = player_y
    else:
        bullet_x = player_x + 20
        bullet_y = player_y

    # Target movement
    for enemy in enemy_list:
        enemy[0] += enemy[2]
        if enemy[0] > SCREEN_WIDTH or enemy[0] < 0:
            enemy[2] *= -1

    # Boss movement
    if boss_active:
        boss_x += boss_speed
        if boss_x < 0 or boss_x > SCREEN_WIDTH - 100:
            boss_speed *= -1

    # Bullet collision with targets
    for enemy in enemy_list:
        if enemy[1] < bullet_y < enemy[1] + 35 and enemy[0] < bullet_x < enemy[0] + 35:
            if enemy[3] == enemyFrozenBLUE:
                player_lives -= 1
            enemy[3] = enemyFrozenBLUE  # Change color to frozen blue
            enemy[2] = 0  # Stop the enemy
            bullet_state = "ready"
            bullet_y = player_y
            score += 1

    # Bullet collision with boss
    if boss_active and boss_y < bullet_y < boss_y + 50 and boss_x < bullet_x < boss_x + 50:
        for enemy in enemy_list:
            if score >= Enemy_COUNT and enemy[3] == enemyFrozenBLUE:
                game_state = "win"
            else:
                game_state = "lose"

    # Draw player, bullet, targets, and boss
    SCREEN.blit(player_img, (player_x, player_y))
    if bullet_state == "fired":
        SCREEN.blit(bullet_img, (bullet_x, bullet_y))
    for enemy in enemy_list:
        enemy_img.fill(enemy[3])  # Set the color of the enemy
        SCREEN.blit(enemy_img, (enemy[0], enemy[1]))
    if boss_active:
        SCREEN.blit(boss_img, (boss_x, boss_y))

    # Draw lives and timer
    for i in range(player_lives):
        pygame.draw.rect(SCREEN, healthYELLOW, (10 + i * 30, 10, 20, 20))
    display_text(f"Time: {time_remaining}", SCREEN_WIDTH - 200, 10)

    # Update game state
    if time_remaining <= 0 or player_lives <= 0:
        game_state = "lose"

    if game_state != "playable":
        display_text("You Win!" if game_state == "win" else "Game Over", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2)
        pygame.display.update()
        pygame.time.delay(2000)
        reset_game()

    # Timer countdown
    current_time = pygame.time.get_ticks()
    if current_time - last_time >= 1000:
        time_remaining -= 1
        last_time = current_time

    # Update display
    pygame.display.update()
    clock.tick(60)