import asyncio
from zeroconf.asyncio import AsyncZeroconf
from zeroconf import ServiceInfo
import socket

service_type = "_pygame._udp.local."
service_name = "gameserver._pygame._udp.local."

default_port = 11337

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('127.0.0.1', 1))  # connect() for UDP doesn't send packets
    return s.getsockname()[0]

async def register_service(service_info):
    zeroconf = AsyncZeroconf()
    await zeroconf.async_register_service(info=service_info, strict=False)
    while True:
        await asyncio.sleep(0.1)

def make_service_info(port = default_port, name = service_name):
    return ServiceInfo(
        type_=service_type,
        name=name,
        port=port,
        addresses=["127.0.0.1"]
    )

