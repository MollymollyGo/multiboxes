import asyncio
import pytest
from multibox.game_server import initialize, init_main

@pytest.mark.asyncio
async def test_server_runs():
    # Run the server initialization in a separate task
    initialize()
    server_task = asyncio.create_task(init_main())

    # Allow some time for the server to start
    await asyncio.sleep(1)

    # Check if the server task is still running
    assert not server_task.done()

    # Cancel the server task to clean up
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass