import json
import logging
import time
import traceback
from collections import defaultdict
from queue import Queue
from threading import Thread
from typing import Optional, Mapping

import requests
from requests import RequestException, Timeout


from config import CONFIG as f

TELEGRAM_APIKEY = f['TELEGRAM_API_KEY']
TELEGRAM_CHAT_IDS = f.get('TELEGRAM_CHAT_IDS', [])
TELEGRAM_ENDPOINT = "https://api.telegram.org/bot"

logger = logging.getLogger('TELEGRAM')


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
                logger.debug("Resetting request for long polling...")
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
                    logger.error("error in calling Telegram: %s", resp)
            finally:
                # give the server a little breath.
                time.sleep(poll_frequence)

    def call_telegram(self, method: str, **kwargs):
        url = "{}{}/{}".format(self.endpoint, self.apikey, method)
        try:
            resp = requests.post(url, kwargs)
        except RequestException as e:
            logger.error('error in calling telegram:\n%s', traceback.format_exc())
            return {'ok': False, 'uncaught_exception': e}
        return resp.json()


class TelegramLogHandler(logging.Handler):

    def __init__(self, logger_mask, level=logging.NOTSET, disable_notification: Optional[Mapping] = None):
        '''
            logger mask is a Mapping logger_name: logger_level
            every log of logger_name with logger_level >= the one passed will be emitted as a telegram message
        '''
        super().__init__(level=level)
        self.disable_notification = disable_notification or {}
        self.logger_mask = logger_mask
        self.api = Api()
        self.log_queue = Queue()
        if TELEGRAM_CHAT_IDS:
  #          Thread(daemon=True, target=self.api.get_updates, args=(self.set_engine_activity,)).start()
  #          Thread(daemon=True, target=self.send_log_messages).start()
            pass

    # def set_engine_activity(self, chat_id, text):
    #     if not self.engine:
    #         self.api.call_telegram('sendMessage', chat_id=chat_id, text='engine not configured!')
    #     if text == 'EMERGENCY STOP ENGINE':
    #         self.engine.activity = Activity.EMERGENCY_STOP
    #         self.api.call_telegram('sendMessage', chat_id=chat_id, text='engine set to emergency stop')
    #     elif text == 'PAUSE ENGINE':
    #         self.engine.activity = Activity.PAUSE
    #         self.api.call_telegram('sendMessage', chat_id=chat_id, text='engine set to pause')
    #     elif text == 'RESTART ENGINE':
    #         self.engine.activity = Activity.TRADE
    #         self.api.call_telegram('sendMessage', chat_id=chat_id, text='engine set to trade')
    #     else:
    #         logger.error('unsupported command: %s', text)
    #         self.api.call_telegram('sendMessage', chat_id=chat_id, text='unsupported command!')

    def filter(self, record):
        try:
            v = self.logger_mask[record.name]
        except KeyError:
            return False
        return record.levelno >= v

    def emit(self, record):
        if TELEGRAM_CHAT_IDS:
            # avoid to memory leak if no recipient is defined
            self.log_queue.put_nowait(record)

    def send_log_messages(self):
        sentinel = object()
        while True:
            messages = []
            notification = False
            self.log_queue.put(sentinel)
            for el in iter(self.log_queue.get_nowait, sentinel):
                messages.append(el.getMessage())
                if not self.disable_notification.get(el.name, False):
                    notification = True
            if messages:
                text = messages if len(messages) == 1 else '\n'.join(
                    '<b>{}.</b> {}'.format(i + 1, m) for i, m in enumerate(messages))
                for user in TELEGRAM_CHAT_IDS:
                    self.api.call_telegram('sendMessage',
                                           chat_id=user,
                                           text=text,
                                           parse_mode='HTML',
                                           disable_notification=not notification
                    )
            time.sleep(5)


class TelegramRunner(object):

    def __init__(self, chat_id):
        self.api = Api()
        self.chat_id = chat_id
        self.inbound_queue = Queue()
        Thread(daemon=True, target=self.api.get_updates, args=(self.receive_message,)).start()

    def send_message(self, text):
        self.api.call_telegram('sendMessage', chat_id=self.chat_id, text=text)

    def receive_message(self, chat_id, text):
        self.inbound_queue.put_nowait(text)

    def get_messages(self):
        sentinel = object()
        while True:
            self.log_queue.put(sentinel)
            messages = []
            for el in iter(self.log_queue.get_nowait, sentinel):
                messages.append(el)
            if messages:
                yield '\n'.join(messages)
            sleep(1)
