import traceback

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import UserContent, Part

from ..root_agent.agent_async import get_agent_async

from .bot import TelegramRunner, TELEGRAM_CHAT_IDS

APP_NAME = 'telegram-dnd-bot'


async def main():
    root_agent, toolset = await get_agent_async()
    session_service = InMemorySessionService()

    tr = await TelegramRunner.create(TELEGRAM_CHAT_IDS, session_service, APP_NAME)
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service
    )

    print('started')
    tr.connect()
    print('telegram runner created')
    async for el in tr.get_messages():
        chat_id, session, message = el
        print(chat_id, 'user input:', message)
        content = UserContent(parts=[Part(text=message)])
        try:
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
        except Exception:
            traceback.print_exc()
            tr.send_message(chat_id, 'una richiesta ha mandato in crisi l\'agente, proviamo a continuare come se niente fosse')

    # Cleanup is handled automatically by the agent framework
    # But you can also manually close if needed:
    print("Closing MCP server connection...")
    await toolset.close()
    print("Cleanup complete.")
