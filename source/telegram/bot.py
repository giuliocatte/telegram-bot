import time
import traceback
from queue import Queue
from threading import Thread

import requests
from requests import RequestException, Timeout


from config import CONFIG as f

TELEGRAM_APIKEY = f['TELEGRAM_API_KEY']
TELEGRAM_CHAT_IDS = f.get('TELEGRAM_CHAT_IDS', [])
TELEGRAM_ENDPOINT = "https://api.telegram.org/bot"


class Api(object):

    def __init__(self, apikey=TELEGRAM_APIKEY, endpoint=TELEGRAM_ENDPOINT):
        self.apikey = apikey
        self.endpoint = endpoint

    def get_updates(self, callback, timeout=60, poll_frequence=3, allowed_updates=('message', )):
        if not TELEGRAM_CHAT_IDS:
            # avoid to delete messages if no one can read them
            return
        update_id = None
        first_call = True
        while True:
            try:
                resp = self.call_telegram("getUpdates", timeout=timeout, offset=update_id, allowed_updates=allowed_updates)
            except Timeout:
                print("Resetting request for long polling...")
            else:
                if resp['ok']:
                    if resp['result']:
                        if first_call:
                            # deleting previous messages on first call
                            update_id = max(message['update_id'] for message in resp['result']) + 1
                        else:
                            for message in resp['result']:
                                if (uid := message['update_id']) >= update_id:
                                    update_id = uid + 1
                                message = message.get('message', {})
                                if (cid := message.get('chat', {}).get('id')) in TELEGRAM_CHAT_IDS and (t := message.get('text')):
                                    callback(cid, t)
                    first_call = False
                else:
                    print("error in calling Telegram: %s", resp)
            finally:
                # give the server a little breath.
                time.sleep(poll_frequence)

    def call_telegram(self, method: str, **kwargs):
        url = "{}{}/{}" .format(self.endpoint, self.apikey, method)
        try:
            resp = requests.post(url, kwargs)
        except RequestException as e:
            print('error in calling telegram:\n%s', traceback.format_exc())
            return {'ok': False, 'uncaught_exception': e}
        return resp.json()


class TelegramRunner(object):

    def __init__(self, chat_ids, session_service, app_name):
        self.api = Api()
        self.session_service = session_service
        self.chat_ids = set(chat_ids)
        self.sessions = {}
        self.app_name = app_name
        self.inbound_queue = {c:Queue() for c in chat_ids}
        Thread(daemon=True, target=self.api.get_updates, args=(self.receive_message,)).start()

    @classmethod
    async def create(cls, chat_ids, session_service, app_name):
        self = cls(chat_ids, session_service, app_name)
        for c in self.chat_ids:
            self.sessions[c] = await session_service.create_session(
                app_name=app_name,
                user_id='chat_{}'.format(c)
            )
        return self

    def send_message(self, chat_id, text):
        self.api.call_telegram('sendMessage', chat_id=chat_id, text=text)

    def receive_message(self, chat_id, text):
        if chat_id in self.chat_ids:
            self.inbound_queue[chat_id].put_nowait(text)
        else:
            self.send_message(chat_id, 'chat id not connected: {}'.format(chat_id))

    async def get_messages(self):
        sentinel = object()
        while True:
            if not self.chat_ids:
                break
            to_disconnect = []
            for chat_id in self.chat_ids:
                self.inbound_queue[chat_id].put(sentinel)
                messages = []
                for el in iter(self.inbound_queue[chat_id].get_nowait, sentinel):
                    print('processing element', el)
                    if el.startswith('/ask'):
                        parts = el.split(' ', 1)
                        if len(parts) > 1:
                            messages.append(parts[1])
                    elif el.startswith('/stop'):    
                        to_disconnect.append(chat_id)
                    elif el.startswith('/restart'):
                        self.sessions[chat_id] = await self.session_service.create_session(
                            app_name=self.app_name,
                            user_id='chat_{}'.format(chat_id)
                        )
                        print('restarted')
                    else:
                        messages.append(el)  # chat diretta
                    if messages:
                        yield (chat_id, self.sessions[chat_id], '\n'.join(messages))
            for c in to_disconnect:
                self.disconnect(c)
            time.sleep(1)

    def connect(self):
        for c in self.chat_ids:
            self.send_message(c, 'ehilà, mi sono connesso!')

    def disconnect(self, chat_id=None):
        print('richiesta di disconnessione per il chat_id', chat_id)
        chat_ids = [chat_id] if chat_id else list(self.chat_ids)
        for c in chat_ids:
            self.send_message(c, 'ciao, mi spengo!')
            self.chat_ids.discard(c)
