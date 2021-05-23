#!/usr/bin/env python
# coding: utf-8
import requests
from binance.client import Client
import matplotlib.pyplot as plt
import configparser
import yaml
import os
import inspect, os.path


# Config matplotlib
plt.rcParams["figure.figsize"] = (15,8)

# Path files
filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))

BOT_PATH = path + "/../binance-trade-bot/"
COINLIST_PATH_FILE = BOT_PATH + "supported_coin_list"
CFG_FL_NAME = BOT_PATH + "user.cfg"
APPRISE_PATH_FILE = BOT_PATH + "config/apprise.yml"

CONFIG_PATH_FILE = path + "/config"

# Starting timestamp
CFG_SECTION = "config"
config = configparser.ConfigParser()
if not os.path.exists(CONFIG_PATH_FILE):
    print("No configuration file (config) found!")
    exit(1)
else:
    config.read(CONFIG_PATH_FILE)

min_timestamp = int(os.environ.get("MIN_TIMESTAMP") or config.get(CFG_SECTION, "min_timestamp"))

# Load user.cfg
USER_CFG_SECTION = "binance_user_config"
user_config = configparser.ConfigParser()
if not os.path.exists(CFG_FL_NAME):
    print("No configuration file (user.cfg) found!")
    exit(1)
else:
    user_config.read(CFG_FL_NAME)

BINANCE_API_KEY = os.environ.get("API_KEY") or user_config.get(USER_CFG_SECTION, "api_key")
BINANCE_API_SECRET_KEY = os.environ.get("API_SECRET_KEY") or user_config.get(USER_CFG_SECTION, "api_secret_key")

# Load Telegram bot info
apprise_conf = {}
with open(APPRISE_PATH_FILE, 'r') as file:
    apprise_conf = yaml.safe_load(file)

url_info = []
for url in apprise_conf['urls']:
    if url.split('/')[0] == 'tgram:':
        url_info = url.split('/')

if len(url_info) == 0:
    exit(0)

TOKEN = url_info[2]
CHAT_ID = url_info[3]

# Load coin list
exchange_crypto = []
if os.path.exists(COINLIST_PATH_FILE):
    with open(COINLIST_PATH_FILE) as rfh:
        for line in rfh:
            line = line.strip()
            if not line or line.startswith("#") or line in exchange_crypto:
                continue
            exchange_crypto.append(line)

print('There are '+str(len(exchange_crypto))+' crypto!')

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET_KEY)

def sendImage():
    url = "https://api.telegram.org/bot"+TOKEN+"/sendPhoto";
    files = {'photo': open('graph.png', 'rb')}
    data = {'chat_id' : CHAT_ID}
    r= requests.post(url, files=files, data=data)

def filledOrder(order):
    return order["status"] == 'FILLED' and order["side"] == 'BUY' and order["time"] >= min_timestamp

def mapOrder(order):
    return float(order["executedQty"])


for crypto in range(0, len(exchange_crypto)):
    orders = client.get_all_orders(symbol=exchange_crypto[crypto]+'USDT')
    
    orders = list(filter(filledOrder, orders))
    orders = list(map(mapOrder, orders))
    
    perc = round(((orders[-1] - orders[0])/orders[0])*100, 3) if len(orders) > 0 else 0.0
    perc_str = "+"+str(perc) if perc > 0 else str(perc)
    
    plt.subplots_adjust(left=None, bottom=None, right=None, top=3, wspace=None, hspace=None)
    plt.subplot(int(len(exchange_crypto)/3)+1, 3, crypto+1)
    plt.plot(range(0, len(orders)), orders)
    plt.title(exchange_crypto[crypto]+" ("+perc_str+"%)")

plt.savefig("graph.png", bbox_inches='tight')
sendImage()