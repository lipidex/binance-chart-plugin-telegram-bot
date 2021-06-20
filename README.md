# Coin Progress Chart and Database Backup plugin for Binance Trade Bot

This is a program tool based on [Binance Trade Bot].

The intent of this bot is to retrieve the local database trade information, e.g. the orders since last database reset, and store it for several plotting. If you have also a Telegram Bot account, it will automatically connect to it send the results.
To operate the bot creates a backup of the database to not interfere with the main bot.

## Install

Create the file `config` based on `config.example`.
Insert your path to Binance Trade Bot in `bot_path=your/path/to/binance-trade-bot`

Then run
```
pip3 install -r requirements.txt
```

## Usage

```bash
python3 db_chart.py
```

## Telegram 

The output can be sent to an external service. It detectes the APPRISE file in the bot folder and connect automatically to it.

## Output example


<p align="center">
  <img src = "graph.example.png">
</p>


ATOM: +20.045% <br>
ADA: +10.19% <br>
BAT: +2.254% <br>
BTT: +27.78% <br>
CAKE: 0.0% <br>
DASH: 0.0% <br>
SOL: +18.76% <br>
EOS: 0.0% <br>
ETC: 0.0% <br>
ICX: +16.796% <br>
IOTA: 0.0% <br>
NEO: 0.0% <br>
OMG: +11.353% <br>
ONT: 0.0% <br>
QTUM: 0.0% <br>
TRX: 0.0% <br>
VET: 0.0% <br>
XMR: 0.0% <br>

**Note** : The data shown are not from your binance account. This program is a tool for [Binance Trade Bot] aimed to analize the bot behaviours since the last reset.


[binance trade bot]: https://github.com/edeng23/binance-trade-bot