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
width, height = 700, 400
spawn_margin = 50

def connect_to_server():
    global client
    global local_ip, local_port, local_player
    local_ip = get_ip()
    local_port = random.randint(5000, 10000)
    local_player = Player(
            random.randint(spawn_margin, width-spawn_margin), 
            random.randint(spawn_margin, height+spawn_margin)
        )

    zeroconf = Zeroconf()
    resp = zeroconf.get_service_info(service_type, service_name)
    print(resp)
    server_ip = socket.inet_ntoa(resp.addresses[0])
    client = SimpleUDPClient(server_ip, resp.port)


    client.send_message("/connect", [local_player.id, local_ip, local_port])

async def pygame_event_loop(event_queue):
    while True:
        event = pygame.event.get()
        if event:
            event_queue.put_nowait(event)
        await asyncio.sleep(0.002)

# Main loop
def update_position(address, *args):
    player_id = args[0]
    x, y = args[1], args[2]
    if player_id in moving_objects:
        moving_objects[player_id].set_position(x, y)
        moving_objects[player_id].set_rotation(args[3])
    else:
        moving_objects[player_id] = Player(x, y)

def new_player(address, *args):
    player_id = args[0]
    if player_id not in moving_objects:
        moving_objects[player_id] = Player(50, 100)

async def draw(screen):
    black = 0, 0, 0
    current_time = time.time()
    while True:
        await asyncio.sleep(1/60)
        screen.fill(black)
        for object in moving_objects:
            moving_objects[object].draw(screen)
        pygame.display.flip()

async def handle_events(event_queue):
    velocity = [0, 0]
    while True:        
        if event_queue.qsize() < 1:
            await asyncio.sleep(0.01)
            continue
        else:
            print("found events")

            events = event_queue.get_nowait()

        print(len(events))

        will_exit = [event for event in events if event.type == pygame.QUIT]
        if will_exit:
            break
        velocity = [0, 0]
        angular_velocity = 0
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    print("left pressed")
                    velocity[0] += -1
                elif event.key == pygame.K_RIGHT:
                    velocity[0] += 1
                elif event.key == pygame.K_UP:
                    velocity[1] += -1
                elif event.key == pygame.K_DOWN:
                    velocity[1] += 1
                elif event.key == pygame.K_q:
                    angular_velocity = -1
                elif event.key == pygame.K_e:
                    angular_velocity = 1
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    velocity[0] = 0
                elif event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    velocity[1] = 0
            else:

                print("event", event)
                #pass
        client.send_message("/update_velocity", [local_player.id, velocity[0], velocity[1], angular_velocity])

    asyncio.get_event_loop().stop()


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
    screen = pygame.display.set_mode((width, height))

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