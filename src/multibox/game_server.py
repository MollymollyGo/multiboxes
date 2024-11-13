import asyncio
import pymunk
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
from pythonosc.udp_client import SimpleUDPClient
from .avahi_utils import get_ip, register_service, make_service_info
import socket

async def game_loop():
    while True:
        space.step(1/60)  # Update physics at 60 FPS
        player_positions = {player_id: (body.position.x, body.position.y, body.angle) for player_id, body in players.items()}
        for player_id, body in players.items():
            if body.velocity.length > max_velocity:
                body.velocity = body.velocity.normalized() * max_velocity
        #print(player_positions)  # Replace with actual network sending logic
        for client in clients:
            for player_id, position in player_positions.items():                
                asyncio.get_event_loop().run_in_executor(None, client.send_message, "/update_position", [player_id, *position])
        await asyncio.sleep(1/60)

def create_player(address, *args):
    player_id = args[0]
    body = pymunk.Body()
    body.position = 50, 100
    body.moment = pymunk.moment_for_box(10, (50, 50))
    poly = pymunk.Poly.create_box(body)
    poly.mass = 10
    poly.elasticity = 0.95
    poly.friction = 0.8
    space.add(body, poly)
    players[player_id] = body

    print(f"Player {player_id} connected")

    # Create the client to send updates to the player
    client_ip = args[1]
    client_port = args[2]
    client = SimpleUDPClient(client_ip, client_port)
    clients.add(client)

def update_player_velocity(address, *args):
    player_id = args[0]
    x, y = args[1], args[2]
    if player_id in players:
        if abs(x) > 0 or abs(y) > 0:
            players[player_id].apply_force_at_world_point(
                force=(x*speed_factor, y*speed_factor),
                point=(players[player_id].position.x, players[player_id].position.y)
            )

def create_space():
    global space
    space = pymunk.Space()
    space.gravity = 0, 98

    walls = []
    walls.append(pymunk.Segment(space.static_body, (0, 0), (0, 400), 0.0))
    walls.append(pymunk.Segment(space.static_body, (700, 0), (700, 400), 0.0))
    walls.append(pymunk.Segment(space.static_body, (0, 0), (700, 0), 0.0))
    walls.append(pymunk.Segment(space.static_body, (0, 400), (700, 400), 0.0))
    for wall in walls:
        wall.elasticity = 0.95
        wall.friction = 0.8
        space.add(wall)

async def init_main():
    dispatcher = Dispatcher()    
    dispatcher.map("/update_velocity", update_player_velocity)
    dispatcher.map("/connect", create_player)
    service_info = make_service_info()
    asyncio.ensure_future(register_service(service_info))
    ip_string = socket.inet_ntoa(service_info.addresses[0])
    server = AsyncIOOSCUDPServer((ip_string,service_info.port), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()
    await game_loop()
    transport.close()

def initialize():
    
    # Set to store the connected clients
    global clients, players
    clients = set()
    players = {}

    global max_velocity, speed_factor
    max_velocity = 200
    speed_factor = 1000

    create_space()


if __name__ == "__main__":
    initialize()
    asyncio.run(init_main())