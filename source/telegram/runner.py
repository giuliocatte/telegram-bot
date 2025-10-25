
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import UserContent, Part

from ...root_agent.agent import root_agent, APP_NAME

from .bot import TelegramRunner, TELEGRAM_CHAT_IDS

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=InMemorySessionService()
)
print(f"Runner created for agent {runner.agent.name}")


async def main():
    session = await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id='test_user'
    )
    print('started')
    tr = TelegramRunner(TELEGRAM_CHAT_IDS[0])
    print('telegram runner created')
    for message in tr.get_messages():      
        print('user input', message)
        if message.lower() in ['bye', 'quit', 'exit', 'stop', 'addio']:
            print('fine')
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
                    tr.send_message(p)
