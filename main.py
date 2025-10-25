
import asyncio
from dotenv import load_dotenv
from source.telegram.runner import main as bot


def main():
    load_dotenv('source/root_agent/.env')
    asyncio.run(bot())


if __name__ == "__main__":
    main()


# if __name__ == '__main__':
#   try:
#     asyncio.run(async_main())
#   except Exception as e:
#     print(f"An error occurred: {e}")