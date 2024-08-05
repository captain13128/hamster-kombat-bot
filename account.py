import base64
import datetime
import logging
import random
import time

from hamster_kombat import HamsterKombatAPI, HamsterKombatUtils

from utils import BikeRidePromo, handle_error, BColors
import config


class Account:
    name: str
    bearer_token: str
    user_agent: str

    balance_coins: int
    spend_tokens: int
    profit_per_hour: int
    balance_keys: int
    total_keys: int

    available_taps: int
    max_taps: int
    earn_per_tap: int

    earn_passive_per_hour: int
    _account_data: dict

    max_card_price: int = 999_999_999_999
    target_balance: int
    cooldown_after_auto_upgrade: int

    parallel_update: bool

    auto_tap: bool
    auto_daily_cipher: bool
    auto_minigame: bool
    auto_upgrade: bool
    auto_promos: bool
    auto_task: bool

    api: HamsterKombatAPI

    BIKE_RIDE_PROMO = "43e35910-c168-4634-ad4f-52fd764a843f"
    SUPPORTED_PROMO = [BIKE_RIDE_PROMO, ]

    utils = HamsterKombatUtils

    @property
    def min_profit_coefficient(self):
        return self.utils.profit_coefficient(price=self.target_balance - self.balance_coins,
                                             profit=self.earn_passive_per_hour)

    def log_account_info(self):
        self.logger.info(f"""
                    user name: {self.name},
                    earn passive per hour: {self.earn_passive_per_hour},
                    balance: {self.balance_coins},
                    available taps: {self.available_taps},
                    balance keys: {self.balance_keys},
                """)

    def __init__(self, name: str, bearer_token: str, user_agent: str, log_level: int = logging.INFO):
        self.logger = logging.getLogger(f"HK_account_[{name}]")
        self.logger.setLevel(log_level)

        self.logger.info(f"init account {name}")

        self.name = name
        self.bearer_token = f"Bearer {bearer_token}"
        self.user_agent = user_agent

        self.api = HamsterKombatAPI(api_url="https://api.hamsterkombatgame.io",
                                    auth=self.bearer_token, user_agent=user_agent)
        self.sync_account_data()

        self.config = self.api.config()
        self.tg_data = self.api.me_telegram()

        self.auto_tap = config.AUTO_TAP
        self.auto_promos = config.AUTO_PROMOS
        self.auto_upgrade = config.AUTO_UPGRADE
        self.auto_minigame = config.AUTO_MINIGAME
        self.auto_daily_cipher = config.AUTO_DAILY_CIPHER
        self.parallel_update = config.PARALLEL_UPDATE
        self.auto_task = config.AUTO_TASK

        self.cooldown_after_auto_upgrade = config.COOLDOWN_AFTER_AUTO_UPGRADE
        self.target_balance = config.TARGET_BALANCE

        self.log_account_info()

    @handle_error
    def sync_account_data(self):
        self.logger.info(f"sync account data")
        account_data = self.api.sync()

        if "clickerUser" not in account_data:
            self.logger.error(f"Invalid account data.")
            return False

        if "balanceCoins" not in account_data["clickerUser"]:
            self.logger.error(f"Invalid balance coins.")
            return False

        self._account_data = account_data

        self.balance_coins = account_data["clickerUser"]["balanceCoins"]
        self.available_taps = account_data["clickerUser"]["availableTaps"]
        self.max_taps = account_data["clickerUser"]["maxTaps"]
        self.earn_per_tap = account_data["clickerUser"]["earnPerTap"]

        self.earn_passive_per_hour = account_data["clickerUser"]["earnPassivePerHour"]

        self.balance_keys = account_data["clickerUser"].get("balanceKeys", 0)
        self.total_keys = account_data["clickerUser"].get("totalKeys", 0)

        self.spend_tokens = 0
        self.profit_per_hour = self.earn_passive_per_hour

        return account_data

    @handle_error
    def boost_full_available_taps(self):
        self.logger.info(f"checking for free tap boost")

        boost_list = list(filter(
            lambda x: x.get("price", -1) == 0 and x.get("id", "") == "BoostFullAvailableTaps",
            self.api.boosts_to_buy_list()
        ))

        if len(boost_list) < 1:
            self.logger.info(BColors.okblue(f"no free boosts available"))
            return False

        boost = boost_list[0]
        if boost.get("cooldownSeconds", 999999) == 0:
            self.logger.info(f"free boost found, attempting to buy")
            time.sleep(random.randint(5, 15))
            self.api.buy_boost(boost["id"])
            self.logger.info(BColors.okblue(f"free boost bought successfully"))
            return True

    @handle_error
    def buy_card(self, card):
        buy_card = self.api.buy_upgrade(card["id"])

        cooldown_seconds = list(filter(lambda x: x["id"] == card["id"], buy_card["upgradesForBuy"]))[0]["cooldownSeconds"]
        self.cooldown_after_auto_upgrade = min(self.cooldown_after_auto_upgrade, cooldown_seconds)
        self.logger.info(BColors.okcyan(
            f"Set timeout {self.cooldown_after_auto_upgrade}s  to next update cooldown_after_auto_upgrade"
        ))

        if buy_card:
            self.logger.info(BColors.okblue(f"card bought successfully"))
            self.sync_account_data()
            time.sleep(random.randint(3, 7))
            # self.balance_coins -= card["price"]
            # self.profit_per_hour += card["profitPerHourDelta"]
            self.spend_tokens += card["price"]
            # self.earn_passive_per_hour += card["profitPerHourDelta"]

            return True
        return False

    @handle_error
    def buy_best_card(self):
        self.logger.info(f"checking for best card")
        time.sleep(random.randint(2, 10))

        upgrades = list(filter(
            lambda x: not x["isExpired"] and x["isAvailable"] and x["profitPerHourDelta"] > 0
                      and x["price"] <= self.max_card_price
                      and self.utils.profit_coefficient(x["price"],
                                                        x["profitPerHourDelta"]) >= self.min_profit_coefficient,
            self.api.upgrades_for_buy().get("upgradesForBuy", [])
        ))
        upgrades.sort(
                key=lambda x: self.utils.profit_coefficient(x["price"], x["profitPerHourDelta"]), reverse=True
            )

        self.logger.info(f"searching for the best upgrades")
        if len(upgrades) == 0:
            self.logger.warning(f"no upgrades available")
            return False
        elif self.parallel_update:
            upgrades = list(filter(lambda x: x.get("cooldownSeconds", 0) == 0, upgrades))
        elif not self.parallel_update and upgrades[0].get("cooldownSeconds", 0) != 0:
            self.logger.warning(BColors.warning(f"card is on cooldown"))
            return False

        for upgrade in upgrades:
            if self.utils.profit_coefficient(upgrade["price"],
                                             upgrade["profitPerHourDelta"]) >= self.min_profit_coefficient:
                self.logger.info(
                    f"best upgrade is {upgrade['name']} with profit "
                    f"{upgrade['profitPerHourDelta']} and price {upgrade['price']}, Level: {upgrade['level']}"
                )
                if self.balance_coins < upgrade["price"]:
                    self.logger.warning(BColors.warning(f"balance is too low to buy the best card."))
                    return False
                self.logger.info(f"attempting to buy the best card...")
                if self.buy_card(upgrade):
                    time.sleep(random.randint(10, 20))
                    self.logger.info(BColors.okcyan(f"best card purchase completed successfully,"
                                     f" Your profit per hour "
                                     f"increased by {self.utils.number_to_string(self.profit_per_hour)}"
                                     f" coins, Spend tokens: {self.utils.number_to_string(self.spend_tokens)}"))
        return True

    @handle_error
    def start_mini_game(self, tg_id: str):
        game_data = self.api.start_keys_minigame()
        if "dailyKeysMiniGame" not in game_data:
            self.logger.error(f"unable to get daily keys mini game.")
            return False
        elif "remainSecondsToGuess" not in game_data["dailyKeysMiniGame"]:
            self.logger.error(f"unable to get daily keys mini game.")
            return False
        elif game_data["dailyKeysMiniGame"]["isClaimed"] is True:
            self.logger.info(BColors.okblue(f"daily keys mini game already claimed."))
            return True

        wait_time = int(
            game_data["dailyKeysMiniGame"]["remainSecondsToGuess"]
            - random.randint(8, 15)
        )

        if wait_time < 0:
            self.logger.error(f"unable to claim mini game.")
            return

        self.logger.info(f"waiting for {wait_time} seconds, Mini-game will be completed in {wait_time} seconds")
        time.sleep(wait_time)

        cipher = ("0" + str(wait_time) + str(random.randint(10000000000, 99999999999)))[:10] + "|" + str(tg_id)
        cipher_base64 = base64.b64encode(cipher.encode()).decode()
        self.api.claim_daily_keys_minigame(cipher=cipher_base64)
        self.logger.info(BColors.okblue(f"mini game claimed successfully."))

    @handle_error
    def start_playground_game(self):
        self.logger.info(f"starting getting playground games")

        promos = self.api.get_promos()

        for promo in promos.get("promos", []):
            if promo.get("promoId", "") == self.BIKE_RIDE_PROMO:
                bike_ride_promo = BikeRidePromo(user_agent=self.user_agent)
                time.sleep(random.randint(5, 15))
                promo_code = bike_ride_promo.get_key(self.BIKE_RIDE_PROMO)
                if promo_code is None:
                    self.logger.error(
                        f"unable to get Bike Ride 3D in Hamster FAM key."
                    )
                    return False

                self.logger.info(f"bike Ride 3D in Hamster FAM key: {promo_code}")
                time.sleep(random.randint(5, 15))
                self.logger.info(f"claiming Bike Ride 3D in Hamster FAM...")
                self.api.apply_promo(promo_code=promo_code)
                self.logger.info(BColors.okblue(f"playground game claimed successfully."))

    def check_play_ground_game_state(self, promo, promos):
        if not self.config["auto_playground_games"]:
            self.logger.info(f"playground games are disabled.")
            return False

        if promo["promoId"] not in self.SUPPORTED_PROMO:
            return False

        if "states" not in promos:
            return True

        for state in promos["states"]:
            if state["promoId"] == promo["promoId"] and state["receiveKeysToday"] >= promo["keysPerDay"]:
                return False

        return True

    @handle_error
    def daily_cipher(self):
        self.logger.info(f"decoding daily cipher")
        cipher = self.config.get("dailyCipher", {}).get("cipher", None)
        if cipher is None:
            return False
        elif self.config.get("dailyCipher", {}).get("isClaimed", True):
            self.logger.info(BColors.okblue(f"daily cipher already claimed"))
            return True
        cipher = self.utils.daily_cipher_decode(cipher)
        self.logger.info(f"daily cipher: {cipher}")
        morse_code = self.utils.text_to_morse_code(cipher)
        self.logger.info(f"daily cipher: {cipher} and Morse code: {morse_code}")

        self.api.claim_daily_cipher(morse_code)
        self.logger.info(BColors.okblue(f"successfully claimed daily cipher"))
        return True

    @handle_error
    def start_tap(self):
        self.logger.info(f"Starting to tap")
        time.sleep(random.randint(5, 15))
        remains = self.available_taps - int(self.available_taps / self.earn_per_tap) * self.earn_per_tap
        tap = self.api.tap(int(self.available_taps / self.earn_per_tap), remains)
        self.logger.info(BColors.okblue(f"Tapping completed successfully."))
        return True

    @handle_error
    def completing_task(self, task):
        self.logger.info(f"run {task['id']}")
        if task["isCompleted"] is True:
            self.logger.info(BColors.okblue(f"{task['id']} task already completed."))
            return True
        else:
            self.logger.info(f"Attempting to complete {task['id']} task")
            reward_coins = task["rewardCoins"]
            time.sleep(random.randint(2, 10))
            self.api.check_task(task_id=task['id'])
            self.logger.info(BColors.okblue(
                f"task completed successfully, Reward coins: {self.utils.number_to_string(reward_coins)}"
            ))
            return True

    @handle_error
    def start_complete_tasks(self):
        self.logger.info(f"start complete all available tasks")

        tasks = self.api.list_tasks()
        if not isinstance(tasks.get("tasks"), list):
            self.logger.error(f"failed get task list")
            return False

        return all(list(map(
            self.completing_task,
            filter(lambda x: "https://" in x.get("link", "") or x["id"] == "streak_days", tasks["tasks"])
        )))

    def start(self):
        time.sleep(random.randint(10, 60))
        self.logger.info("Start account")
        while True:
            day = datetime.datetime.now().day
            my_ip = self.api.ip()
            self.logger.info(BColors.header(
                f"account ip: {my_ip['ip']}; company: {my_ip['asn_org']}; country: {my_ip['country_code']}"
            ))

            if self.auto_daily_cipher is True:
                self.daily_cipher()
                time.sleep(random.randint(10, 30))
            if self.auto_minigame is True:
                self.start_mini_game(tg_id=self.tg_data.get("telegramUser", {}).get("authUserId"))
                time.sleep(random.randint(10, 30))
            if self.auto_promos is True:
                self.start_playground_game()
                time.sleep(random.randint(10, 30))
            if self.auto_task is True:
                self.start_complete_tasks()
                time.sleep(random.randint(10, 30))

            while True:
                self.cooldown_after_auto_upgrade = config.COOLDOWN_AFTER_AUTO_UPGRADE
                if self.sync_account_data():
                    if self.auto_upgrade is True:
                        if self.auto_tap is True:
                            self.start_tap()
                            time.sleep(random.randint(10, 30))

                        self.buy_best_card()

                        self.log_account_info()
                        time.sleep(self.cooldown_after_auto_upgrade)

                if day != datetime.datetime.now().day:
                    self.config = self.api.config()
                    break
