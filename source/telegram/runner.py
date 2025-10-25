
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import UserContent, Part

from ..root_agent.agent_async import get_agent_async

from .bot import TelegramRunner, TELEGRAM_CHAT_IDS

APP_NAME = 'telegram-dnd-bot'


async def main():
    root_agent, toolset = await get_agent_async()
    session_service = InMemorySessionService()

    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id='test_user'
    )    
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service
    )

    print('started')
    tr = TelegramRunner(TELEGRAM_CHAT_IDS)
    tr.connect()
    print('telegram runner created')
    for chat_id, message in tr.get_messages():      
        print('user input', message)
        if message.lower() in ['bye', 'quit', 'exit', 'stop', 'addio']:
            print('fine')
            tr.disconnect()
            break
        content = UserContent(parts=[Part(text=message)])
        async for event in runner.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=content
            ):
            for part in event.content.parts:
                p = part.text
                if p:
                    print('sending answer', p)
                    tr.send_message(chat_id, p)

    # Cleanup is handled automatically by the agent framework
    # But you can also manually close if needed:
    print("Closing MCP server connection...")
    await toolset.close()
    print("Cleanup complete.")
