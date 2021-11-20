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
import datetime
import math

### METHODS ###
# Define functions
def sendImage(photoname,token,chat_id):
    url = "https://api.telegram.org/bot"+token+"/sendPhoto";
    files = {'photo': open(photoname, 'rb')}
    data = {'chat_id' : chat_id}
    r= requests.post(url, files=files, data=data)

def draw_grow(xs, ys, grows, labels, title, colors):
    ncols = 3
    if len(xs) <3:
        ncols = len(xs)
    fig, axes = plt.subplots(nrows=int(math.ceil(len(ys)/3)), ncols=3, sharex=True)
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
    
    # define y position of suptitle to be ~20% of a row above the top row
    y_title_pos = axes[0][0].get_position().get_points()[1][1]+(1/int(len(ys)/3))*0.5
    fig.suptitle(title, y=y_title_pos, fontsize=14)
    
def draw_sum(x,y,grow,label, title, colors):
    fig, axes = plt.subplots(nrows=1, ncols=1, sharex=True)
    plt.subplots_adjust(left=None, bottom=None, right=None, top=3, wspace=None, hspace=None)
       
    c = next(colors)["color"]
    axes.title.set_text(title+' ('+grow+'%)')
    axes.plot(x, y, label=label, color=c)
    axes.scatter(x, y, color=c)  # dots
    axes.set_xticks(x)
    axes.grid(False)
    fig.legend(loc="upper left")


### BINANCE ###
def filledOrder(order):
    MIN_TIMESTAMP_BINANCE = int("1518308894652")
    return order["status"] == 'FILLED' and order["side"] == 'BUY' and order["time"] >= MIN_TIMESTAMP_BINANCE

def mapOrder(order):
    return float(order["executedQty"])

def binance_coin_amount(client, exchange_crypto, min_datetime, colors, bridge_binance):

    coin_grow = []
    coin_perc = []
    trades_number = []
    grow_text= ""

    for crypto in range(0, len(exchange_crypto)):
        orders = client.get_all_orders(symbol=exchange_crypto[crypto]+bridge_binance)

        orders = list(filter(filledOrder, orders))
        orders = list(map(mapOrder, orders))

        perc = round(((orders[-1] - orders[0])/orders[0])*100, 3) if len(orders) > 0 else 0.0
        perc_str = "+"+str(perc) if perc > 0 else str(perc)

        coin_grow.append(orders)
        trades_number.append(list(range(1,len(orders)+1)))
        coin_perc.append(perc_str)
        grow_text = grow_text + exchange_crypto[crypto]+": "+(str(orders[0])+" -> "+str(orders[-1])+" ("+perc_str+"%)" if len(orders) >= 2 else "N.A.")+"\n"

    draw_grow(trades_number, coin_grow, coin_perc, exchange_crypto,"Coin amount evolution",colors)
    # Send result
    plt.savefig("graph.png", bbox_inches='tight')
    print(grow_text)

def process_coin_amount(exchange_crypto, min_datetime, cur, colors):
    coin_grow = []
    coin_perc = []
    trades_number = []
    grow_text= ""

    for crypto in range(0,len(exchange_crypto)):        
        order_list = []
        
        # retrieving coin list of orders
        sqlite_select_query = "select alt_trade_amount from trade_history where alt_coin_id=? and state='COMPLETE' and selling=0 and DATE(datetime) > '" + str(min_datetime) +"'"
        
        orders = cur.execute(sqlite_select_query,[exchange_crypto[crypto]])
        
        for order in orders.fetchall():
            order_list.append(order[0])
        
        perc = round(((order_list[-1] - order_list[0])/order_list[0])*100, 3) if len(order_list) > 0 else 0.0
        perc_str = "+"+str(perc) if perc > 0 else str(perc)
        
        coin_grow.append(order_list)
        trades_number.append(list(range(1,len(order_list)+1)))
        coin_perc.append(perc_str)
        grow_text = grow_text + exchange_crypto[crypto]+": "+perc_str+"% \n"
        
    draw_grow(trades_number, coin_grow, coin_perc, exchange_crypto, "Coin amount evolution",colors)

    plt.savefig("graph.png", bbox_inches='tight')
    print("Coin amount")
    print(grow_text)
    

def process_coin_value(exchange_crypto, min_datetime, cur, colors):
    coin_grow = []
    coin_perc = []
    trades_number = []
    grow_text= ""

    for crypto in range(0,len(exchange_crypto)):        
        order_list = []
        
        # retrieving coin list of orders
        sqlite_select_query = "select crypto_trade_amount from trade_history where alt_coin_id=? and state='COMPLETE' and selling=0 and DATE(datetime) > '" + str(min_datetime) +"'"
        orders = cur.execute(sqlite_select_query,[exchange_crypto[crypto]])
        
        for order in orders.fetchall():
            order_list.append(order[0])
        
        perc = round(((order_list[-1] - order_list[0])/order_list[0])*100, 3) if len(order_list) > 0 else 0.0
        perc_str = "+"+str(perc) if perc > 0 else str(perc)
        
        coin_grow.append(order_list)
        trades_number.append(list(range(1,len(order_list)+1)))
        coin_perc.append(perc_str)
        grow_text = grow_text + exchange_crypto[crypto]+": "+perc_str+"% \n"
        
    draw_grow(trades_number, coin_grow, coin_perc, exchange_crypto, "Coin value evolution",colors)

    plt.savefig("graph.png", bbox_inches='tight')
    print("Coin value")
    print(grow_text)
    

def process_fiat_evolution(exchange_crypto, min_datetime, cur, colors):
    # retrieve FIAT evolution
    coin_grow = []
    coin_perc = []
    trades_number = []
    order_list = []
    grow_text= ""
    sqlite_select_query = "select crypto_trade_amount from trade_history where state='COMPLETE' and selling=0 and alt_coin_id <> 'BNB' and DATE(datetime) > '" + str(min_datetime) +"'"
    orders = cur.execute(sqlite_select_query)
    for order in orders.fetchall():
        order_list.append(order[0])

    perc = round(((order_list[-1] - order_list[0])/order_list[0])*100, 3) if len(order_list) > 0 else 0.0
    perc_str = "+"+str(perc) if perc > 0 else str(perc)

    coin_grow.append(order_list)
    trades_number.append(list(range(1,len(order_list)+1)))
    coin_perc.append(perc_str)
    grow_text = grow_text +"FIAT evolution: "+perc_str+"% \n"
    exchange_crypto.clear()
    exchange_crypto.append("SUM")
    draw_sum(trades_number[0], coin_grow[0], perc_str, "SUM", "Overall value evolution [USDT] ",colors)

    plt.savefig("graph2.png", bbox_inches='tight')
    print(grow_text)
    
# Load coin list from the file
def get_coin_list_file(coinlist_file):
    exchange_crypto = []
    if os.path.exists(coinlist_file):
        with open(coinlist_file) as rfh:
            for line in rfh:
                line = line.strip()
                if not line or line.startswith("#") or line in exchange_crypto:
                    continue
                exchange_crypto.append(line)
    
    return exchange_crypto 

# Load active coin list from the db
def get_coin_list_db(min_datetime, cur):
    exchange_crypto = []

    sqlite_select_query = "select distinct alt_coin_id from trade_history where state='COMPLETE' and selling=0 and DATE(datetime) > '" + str(min_datetime) +"'"
    active_coins = cur.execute(sqlite_select_query)
    
    for coin in active_coins:
        exchange_crypto.append(coin[0])
        
    return exchange_crypto 
