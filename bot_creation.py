'''
	To have telegram bot working properly:
	1. create the bot using telegram @BotFather
	2. copy the bot api key in config.json file, in key TELEGRAM_API_KEY
	3. write a chat message to your bot on telegram
	4. run this module and look at the printed response, for your chat id
	5. copy that chat id into the config.json file, in a list on key TELEGRAM_CHAT_IDS
	6. if other people needs to control the bot, more chat ids can be added to this list in the same way
'''
from source.telegram.bot import Api


if __name__ == "__main__":
	a = Api()
	resp = a.call_telegram("getUpdates")
	print(resp)


