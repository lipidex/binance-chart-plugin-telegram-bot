from db_chart import *

import shutil
import datetime
import configparser
import sqlite3
import yaml
import requests
import os
import sys
import inspect, os.path
import matplotlib.pyplot as plt
from binance.client import Client

if len(sys.argv) != 2 or not (sys.argv[1] == "-bn" or sys.argv[1] == "-db"):
    print("You need to specify one of these modality:\n -bn     Generate chart with Binance history orders\n -db     Generate chart with database bot history orders")
    exit(1)

# Path files
filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))

CONFIG_PATH_FILE = path + "/config"

CFG_SECTION = "config"
config = configparser.ConfigParser()
if not os.path.exists(CONFIG_PATH_FILE):
    print("No configuration file (config) found!")
    exit(1)
else:
    config.read(CONFIG_PATH_FILE)
    
BOT_PATH = os.environ.get("bot_path") or config.get(CFG_SECTION, "bot_path")
ORIGINAL_DB_PATH = BOT_PATH + "/data/crypto_trading.db"
DB_PATH = BOT_PATH + "/data/crypto_trading.db.backup"
CFG_FL_NAME = BOT_PATH + "/user.cfg"
COINLIST_PATH_FILE = BOT_PATH + "/supported_coin_list"
APPRISE_PATH_FILE = BOT_PATH + "/config/apprise.yml"

# Retrieve data from config file
min_datetime = str(config.get(CFG_SECTION, "min_datetime"))
try:
    assert datetime.datetime.strptime(min_datetime, "%Y-%m-%d")
except:
    min_datetime = ""
    print("Wrong date format (expecting YYYY-MM-DD); Display everything.")

try:
    enable_fiat_evolution = config.get(CFG_SECTION, "enable_fiat_evolution") == "1"
except:
    enable_fiat_evolution = 0
    
try:
    enable_coin_value = config.get(CFG_SECTION, "enable_coin_value") == "1"
except:
    enable_coin_value = 0
    
original = ORIGINAL_DB_PATH
target = DB_PATH

if not os.path.exists(DB_PATH):
    print("No backup database (crypto_trading.db.backup) found, creating one...")
    f = open(DB_PATH,'w')

shutil.copyfile(original, target)

# Config matplotlib
plt.rcParams["figure.figsize"] = (15,8)
colors = plt.rcParams["axes.prop_cycle"]()

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

exchange_crypto = []
exchange_crypto = get_coin_list(COINLIST_PATH_FILE)

if sys.argv[1] == "-bn":
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

    BRIDGE_BINANCE = os.environ.get("BRIDGE_BINANCE") or config.get(CFG_SECTION, "bridge_binance") or "USDT"

    client = Client(BINANCE_API_KEY, BINANCE_API_SECRET_KEY)
    binance_coin_amount(client,exchange_crypto,min_datetime,colors,BRIDGE_BINANCE)
    sendImage("graph.png",TOKEN,CHAT_ID)

elif sys.argv[1] == "-db":
    # create con object to connect 
    # the database geeks_db.db
    con = sqlite3.connect(DB_PATH)
      
    # create the cursor object
    cur = con.cursor()
    process_coin_amount(exchange_crypto,min_datetime,cur,colors)
    sendImage("graph.png",TOKEN,CHAT_ID)
    if enable_coin_value:
        process_coin_value(exchange_crypto,min_datetime,cur,colors)
        sendImage("graph.png",TOKEN,CHAT_ID)
    if enable_fiat_evolution:
        process_fiat_evolution(exchange_crypto,min_datetime,cur,colors)
        sendImage("graph2.png",TOKEN,CHAT_ID)

    cur.close()


