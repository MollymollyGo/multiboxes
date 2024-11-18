import pygame
import asyncio
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
from pythonosc.udp_client import SimpleUDPClient
from .player import Player
import time
import random
from .avahi_utils import get_ip, service_type, service_name
from zeroconf import Zeroconf
import socket

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

def connect_to_server():
    global client
    global local_ip, local_port, local_player
    local_ip = "127.0.0.1"
    local_port = random.randint(5000, 10000)
    local_player = Player(random.randint(player_x, player_x + 10), random.randint(player_y, player_y), player_img)

    zeroconf = Zeroconf()
    resp = zeroconf.get_service_info(service_type, service_name)
    print(resp)
    server_ip = "127.0.0.1"
    client = SimpleUDPClient(server_ip, 11337)

    client.send_message("/connect", [local_player.id, local_ip, local_port])

async def pygame_event_loop(event_queue):
    while True:
        event = pygame.event.get()
        if event:
            event_queue.put_nowait(event)
        await asyncio.sleep(0.002)

def update_position(address, *args):
    player_id = args[0]
    player_x, player_y = args[1], args[2]
    if player_id in moving_objects:
        moving_objects[player_id].set_position(player_x, player_y)
    else:
        moving_objects[player_id] = Player(player_x, player_y, player_img)

def new_player(address, *args):
    player_id = args[0]
    if player_id not in moving_objects:
        moving_objects[player_id] = Player(player_x, player_y, player_img)

async def draw(screen):
    while True:
        await asyncio.sleep(1 / 60)
        SCREEN.fill(canvasGRAY)
        # Drawing player, enemies, bullet and boss
        SCREEN.blit(player_img, (player_x, player_y))
        if bullet_state == "fired":
            SCREEN.blit(bullet_img, (bullet_x, bullet_y))
        for enemy in enemy_list:
            enemy_img.fill(enemy[3])
            SCREEN.blit(enemy_img, (enemy[0], enemy[1]))
        if boss_active:
            SCREEN.blit(boss_img, (boss_x, boss_y))
        pygame.display.flip()

async def handle_events(event_queue):
    global player_x, player_y, bullet_x, bullet_y, bullet_state, score, game_state,boss_speed
    while True:
        if event_queue.qsize() < 1:
            await asyncio.sleep(0.01)
            client.send_message("/update_position", [local_player.id, player_x, player_y])
            continue
        else:
            events = event_queue.get_nowait()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                socket.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and bullet_state == "ready":
                    bullet_x = player_x + 20
                    bullet_state = "fired"
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    socket.exit()
            # Player movement
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and player_x > 0:
                player_x -= player_speed
            if keys[pygame.K_RIGHT] and player_x < SCREEN_WIDTH - 50:
                player_x += player_speed
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

        client.send_message("/update_position", [local_player.id, player_x, player_y])
        pygame.display.update()
        clock.tick(60)

def main():
    loop = asyncio.get_event_loop()
    event_queue = asyncio.Queue()

    dispatcher = Dispatcher()
    dispatcher.map("/update_position", update_position)
    dispatcher.map("/new_player", new_player)

    global moving_objects
    moving_objects = {local_player.id: local_player}

    pygame.init()
    pygame.display.set_caption("pygame+asyncio+server")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    server = AsyncIOOSCUDPServer((local_ip, local_port), dispatcher, asyncio.get_event_loop())

    osc_receive_task = asyncio.ensure_future(server.create_serve_endpoint())
    pygame_task = asyncio.ensure_future(pygame_event_loop(event_queue))
    drawing_task = asyncio.ensure_future(draw(screen))
    event_task = asyncio.ensure_future(handle_events(event_queue))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        pygame_task.cancel()
        drawing_task.cancel()
        osc_receive_task.cancel()
        event_task.cancel()
    pygame.quit()

if __name__ == "__main__":
    connect_to_server()
    main()
