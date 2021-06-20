# Coin Progress Chart and Database Backup plugin for Binance Trade Bot

This is a program tool based on [Binance Trade Bot].

The intent of this bot is to retrieve the local database trade infomation, e.g. the orders since last database reset, and store it for several plottings. If you have also a Telegram Bot account, it will automaticaly connect to it send the results.
To operate the bot creates a backup of the database to not interfere with the main bot

## Install

Create the file `config` based on `config.example`.
Insert your path to Binance Trade Bot in `bot_path=`

Then run
```
pip3 install -r requirements.txt
```

## Usage

```bash
python3 db_chart.py
```

## Telegram 

The output can be sent to an external service. It detectes the APPRISE file in the bot folder and connect automatically to it 

## Output example


<p align="center">
  <img src = "graph.example.png">
</p>


ATOM: +20.045% 
ADA: +10.19% 
BAT: +2.254% 
BTT: +27.78% 
CAKE: 0.0% 
DASH: 0.0% 
SOL: +18.76% 
EOS: 0.0% 
ETC: 0.0% 
ICX: +16.796% 
IOTA: 0.0% 
NEO: 0.0% 
OMG: +11.353% 
ONT: 0.0% 
QTUM: 0.0% 
TRX: 0.0% 
VET: 0.0% 
XMR: 0.0% 

**Note** : The data shown are not from your binance account. This program is a tool for [Binance Trade Bot] aimed to analize the bot behaviours since the last reset.


[binance trade bot]: https://github.com/edeng23/binance-trade-bot
