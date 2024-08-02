import random
import threading
import time

from account import Account
from utils import setup_logging
import config

import logging


logger = logging.getLogger(__name__)
setup_logging()


if __name__ == '__main__':
    threads = []
    # account_data = config.ACCOUNTS[0]
    try:
        for account_data in config.ACCOUNTS:
            account = Account(
                name=account_data["name"],
                bearer_token=account_data["bear_token"],
                user_agent=account_data["user_agent"]
            )
            threads.append(threading.Thread(target=account.start, name=f"{account_data['name']} tg account"))
            time.sleep(random.randint(10, 60))

        list(map(lambda x: x.start(), threads))
        list(map(lambda x: x.join(), threads))
    except Exception as e:
        logger.error(e)
        time.sleep(10)
