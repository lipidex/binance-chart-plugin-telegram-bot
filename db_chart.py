import shutil
import configparser
import sqlite3
import subprocess
import yaml
import requests
import io
import os
import inspect, os.path
import matplotlib.pyplot as plt


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
COINLIST_PATH_FILE = BOT_PATH + "/supported_coin_list"
APPRISE_PATH_FILE = BOT_PATH + "/config/apprise.yml"

original = ORIGINAL_DB_PATH
target = DB_PATH

if not os.path.exists(DB_PATH):
    print("No backup database (crypto_trading.db.backup) found, creating one...")
    f = open(BOT_PATH + "/data/crypto_trading.db.backup",'w')

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

def sendImage():
    url = "https://api.telegram.org/bot"+TOKEN+"/sendPhoto";
    files = {'photo': open('graph.png', 'rb')}
    data = {'chat_id' : CHAT_ID}
    r= requests.post(url, files=files, data=data)

def draw_grow(xs, ys, grows, labels):
    fig, axes = plt.subplots(nrows=int(len(ys)/3), ncols=3, sharex=True)
    plt.subplots_adjust(left=None, bottom=None, right=None, top=3, wspace=None, hspace=None)

    for ax, x, y, grow, label in zip(axes.flat, xs, ys, grows, labels):
        # Get the next color from the cycler
        c = next(colors)["color"]
        
        ax.title.set_text(label+' ('+grow+'%)')
        ax.plot(x, y, label=label, color=c)
        ax.scatter(x, y, color=c)  # dots
        ax.set_xticks(x)
        ax.grid(False)

    fig.legend(loc="upper left")
    
# Load coin list
exchange_crypto = []
if os.path.exists(COINLIST_PATH_FILE):
    with open(COINLIST_PATH_FILE) as rfh:
        for line in rfh:
            line = line.strip()
            if not line or line.startswith("#") or line in exchange_crypto:
                continue
            exchange_crypto.append(line)

# create con object to connect 
# the database geeks_db.db
con = sqlite3.connect(DB_PATH)
  
# create the cursor object
cur = con.cursor()

coin_grow = []
coin_perc = []
trades_number = []
grow_text= ""

for crypto in range(0,len(exchange_crypto)):
    
    order_list = []
    
    # retrieving coin list of orders
    sqlite_select_query = "select alt_trade_amount from trade_history where alt_coin_id=? and state='COMPLETE' and selling=0"
    orders = cur.execute(sqlite_select_query,[exchange_crypto[crypto]])
    
    for order in orders.fetchall():
        order_list.append(order[0])
    
    perc = round(((order_list[-1] - order_list[0])/order[0])*100, 3) if len(order_list) > 0 else 0.0
    perc_str = "+"+str(perc) if perc > 0 else str(perc)
    
    coin_grow.append(order_list)
    trades_number.append(list(range(1,len(order_list)+1)))
    coin_perc.append(perc_str)
    grow_text = grow_text + exchange_crypto[crypto]+": "+perc_str+"% \n"
    
draw_grow(trades_number, coin_grow, coin_perc, exchange_crypto)

plt.savefig("graph.png", bbox_inches='tight')
print(grow_text)
sendImage()

cur.close()
