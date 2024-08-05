# hamster-kombat-bot

Automatic card upgrade, auto-tap, auto-play minigames

## .env variables

You need to specify these env variables to run this bot. If you run it locally, you can also write them in `.env` text
file.

``` bash
MASTER_KOMBAT_VERSION=0.0.5

SEPARATOR=;;
ACCOUNTS_COUNT=3

HK_API_URL=https://api.hamsterkombatgame.io

ACCOUNTS_NAMES=ACC1;;ACC2;;ACC3
ACCOUNTS_BEARER_TOKEN=1111111111853Az36scXo11111111111wbieT9L1111111111qrxq1111111111111Kc71qzYdOV551111111111;;2222222222853Az36scXo22222222222wbieT9L2222222222qrxq2222222222222Kc71qzYdOV552222222222;;3333333333853Az36scXo33333333333wbieT9L3333333333qrxq3333333333333Kc71qzYdOV553333333333
ACCOUNTS_USERAGENT=Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.118 Mobile Safari/537.36 XiaoMi/MiuiBrowser/14.15.1-gn;;Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.118 Mobile Safari/537.36 XiaoMi/MiuiBrowser/14.15.1-gn;;Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.118 Mobile Safari/537.36 XiaoMi/MiuiBrowser/14.15.1-gn

AUTO_TAP=True
AUTO_UPGRADE=True
AUTO_DAILY_CIPHER=False
AUTO_MINIGAME=False
AUTO_PROMOS=False
AUTO_TASK=True

TARGET_BALANCE=18000000000
COOLDOWN_AFTER_AUTO_UPGRADE=7200

```

## run in docker
```bash
docker pull captain13128/hamster-kombat-bot:0.0.1
vim .env # add config

docker-compose up -d
```
config example [here]((https://github.com/captain13128/hamster-kombat-bot/blob/main/.env.example))

## run
```bash
git clone https://github.com/captain13128/hamster-kombat-bot.git
cd hamster-kombat-bot
cp .env.example .env

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## How to find my phone's user agent?

Open this website using your phone's default browser. Please avoid using Chrome, Firefox, Opera, or any other similar browsers. For Samsung devices, open the website using `Samsung Internet`, and for other Android phones, use the respective default Android browser.

For iOS devices, use Safari.

Search [What is my user agent](https://www.google.com/search?q=What+is+my+user+agent) on Google or visit [WhatsMyUA.info](https://www.whatsmyua.info/) to find your default device browser user-agent. Make sure to add it to your account.

For example (do not use this): Windows 11 and Firefox user-agent is: `Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0`
