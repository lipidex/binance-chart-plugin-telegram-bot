import shutil
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

# Load config file
CFG_SECTION = "config"
config = configparser.ConfigParser()
if not os.path.exists(CONFIG_PATH_FILE):
    print("No configuration file (config) found!")
    exit(1)
else:
    config.read(CONFIG_PATH_FILE)

BOT_PATH = (os.environ.get("bot_path") or config.get(CFG_SECTION, "bot_path") or "/../binance-trade-bot")

# All the path necessary
ORIGINAL_DB_PATH = BOT_PATH + "/data/crypto_trading.db"
DB_PATH = BOT_PATH + "/data/crypto_trading.db.backup"
CFG_FL_NAME = BOT_PATH + "/user.cfg"
COINLIST_PATH_FILE = BOT_PATH + "/supported_coin_list"
APPRISE_PATH_FILE = BOT_PATH + "/config/apprise.yml"

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

# Load coin list
exchange_crypto = []
if os.path.exists(COINLIST_PATH_FILE):
    with open(COINLIST_PATH_FILE) as rfh:
        for line in rfh:
            line = line.strip()
            if not line or line.startswith("#") or line in exchange_crypto:
                continue
            exchange_crypto.append(line)

### METHODS ###
# Send result on Telegram
def sendImage():
    url = "https://api.telegram.org/bot"+TOKEN+"/sendPhoto";
    files = {'photo': open('graph.png', 'rb')}
    data = {'chat_id' : CHAT_ID}
    r= requests.post(url, files=files, data=data)

# Plot charts
def draw_grow(ys, grows, labels):
    fig, axes = plt.subplots(nrows=int(len(ys)/3)+1, ncols=3)
    plt.subplots_adjust(left=None, bottom=None, right=None, top=3, wspace=None, hspace=None)
    
    for ax, y, grow, label, i in zip(axes.flat, ys, grows, labels, range(0, len(labels))):
        # Get the next color from the cycler
        c = next(colors)["color"]
        x = list(range(1,len(y)+1))

        ax.title.set_text(label+' ('+grow+'%)')
        ax.plot(x, y, label=label, color=c)
        ax.scatter(x, y, color=c)  # dots
        ax.set_xticks(x)
        ax.grid(False)

    for ax in axes.flat:
        if len(ax.title.get_text()) == 0:
            ax.set_visible(False)
    
    fig.legend(loc="upper left")
    plt.savefig("graph.png", bbox_inches='tight')

grow_text= ""

if sys.argv[1] == "-bn":
    ### BINANCE ###

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

    MIN_TIMESTAMP_BINANCE = int(os.environ.get("MIN_TIMESTAMP_BINANCE") or config.get(CFG_SECTION, "min_timestamp_binance"))
    BRIDGE_BINANCE = os.environ.get("BRIDGE_BINANCE") or config.get(CFG_SECTION, "bridge_binance") or "USDT"

    def filledOrder(order):
        return order["status"] == 'FILLED' and order["side"] == 'BUY' and order["time"] >= MIN_TIMESTAMP_BINANCE

    def mapOrder(order):
        return float(order["executedQty"])

    client = Client(BINANCE_API_KEY, BINANCE_API_SECRET_KEY)

    coin_grow = []
    coin_perc = []

    for crypto in range(0, len(exchange_crypto)):
        orders = client.get_all_orders(symbol=exchange_crypto[crypto]+BRIDGE_BINANCE)

        orders = list(filter(filledOrder, orders))
        orders = list(map(mapOrder, orders))

        perc = round(((orders[-1] - orders[0])/orders[0])*100, 3) if len(orders) > 0 else 0.0
        perc_str = "+"+str(perc) if perc > 0 else str(perc)

        coin_grow.append(orders)
        coin_perc.append(perc_str)
        grow_text = grow_text + exchange_crypto[crypto]+": "+(str(orders[0])+" -> "+str(orders[-1])+" ("+perc_str+"%)" if len(orders) >= 2 else "N.A.")+"\n"

    draw_grow(coin_grow, coin_perc, exchange_crypto)

elif sys.argv[1] == "-db":
    ### DATABASE ###
    original = ORIGINAL_DB_PATH
    target = DB_PATH

    if not os.path.exists(DB_PATH):
        print("No backup database (crypto_trading.db.backup) found, creating one...")
        f = open(BOT_PATH + "data/crypto_trading.db.backup",'w')

    shutil.copyfile(original, target)

    # create con object to connect 
    # the database geeks_db.db
    con = sqlite3.connect(DB_PATH)
    
    # create the cursor object
    cur = con.cursor()

    coin_grow = []
    coin_perc = []

    for crypto in range(0,len(exchange_crypto)):
        
        order_list = []
        
        # retrieving coin list of orders
        sqlite_select_query = "select alt_trade_amount from trade_history where alt_coin_id=? and state='COMPLETE' and selling=0"
        orders = cur.execute(sqlite_select_query,[exchange_crypto[crypto]])
        
        for order in orders.fetchall():
            order_list.append(order[0])
        
        perc = round(((order_list[-1] - order_list[0])/order_list[0])*100, 3) if len(order_list) > 0 else 0.0
        perc_str = "+"+str(perc) if perc > 0 else str(perc)
        
        coin_grow.append(order_list)
        coin_perc.append(perc_str)
        grow_text = grow_text + exchange_crypto[crypto]+": "+(str(order_list[0])+" -> "+str(order_list[-1])+" ("+perc_str+"%)" if len(order_list) >= 2 else "N.A.")+"\n"
        
    draw_grow(coin_grow, coin_perc, exchange_crypto)
    cur.close()

# Send result
print(grow_text)
sendImage()
