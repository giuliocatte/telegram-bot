
import asyncio
from dotenv import load_dotenv
from source.telegram.runner import main as bot


def main():
    load_dotenv('source/root_agent/.env')
    asyncio.run(bot())


if __name__ == "__main__":
    main()
