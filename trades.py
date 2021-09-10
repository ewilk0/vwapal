import requests, json, time, sys, subprocess
import pandas as pd
import datetime as dt
from binance.client import Client
import smtplib, ssl

port = 465
password = "xxx"
context = ssl.create_default_context()
root_url = "https://api.binance.com/api/v1/klines"
multiplier = 0.5
client = Client("xxx", "xxx")
listCoins = []

def findSymbols(coinList, conVal, sym):
	tradingCoin = None
	listCoins = coinList
	print("List: " + str(coinList))
	if conVal == 0:
		pass
	elif conVal == 1:
		del coinList[coinList.index(sym)]
	for coin in coinList:
		url = root_url + '?symbol=' + str(coin) + '&interval=' + '5m' + '&limit=' + '72'
		data = json.loads(requests.get(url).text)
		df = pd.DataFrame(data)
		df.columns = ['open_time',
				 'o', 'h', 'l', 'c', 'v',
				 'close_time', 'qav', 'num_trades',
				 'taker_base_vol', 'taker_quote_vol', 'ignore']
		df.index = [dt.datetime.fromtimestamp(x/1000.0) for x in df.close_time]
		df = df.astype(float)
		df['vwap'] = ((df.v*((df.h+df.l+df.c)/3.00)).cumsum() / df.v.cumsum())
		if df.iloc[71]['vwap']*1.01 > df.iloc[71]['c']:
			if (df.iloc[71]['vwap']*1.01)/df.iloc[71]['c'] <= 1.005:
				tradingCoin = str(coin)
				print("Now trading: " + tradingCoin)
				break
	if tradingCoin == None:
		print("No favorable setups found. Restarting in one minute.")
		time.sleep(60)
		subprocess.Popen(["python3", "scanner.py"])
		sys.exit(0)
	get_bars(tradingCoin, 0, 0)

def get_bars(symbol, conVal, quan):
	get_bars.counter += 1
	if(get_bars.counter >= 300 and conVal != 2):
		subprocess.Popen(["python3", "scanner.py"])
		sys.exit(0)
	url = str(root_url) + '?symbol=' + str(symbol) + '&interval=' + '5m' + '&limit=' + '72'
	data = json.loads(requests.get(url).text)
	df = pd.DataFrame(data)
	df.columns = ['open_time',
				'o', 'h', 'l', 'c', 'v',
				'close_time', 'qav', 'num_trades',
				'taker_base_vol', 'taker_quote_vol', 'ignore']
	df.index = [dt.datetime.fromtimestamp(x/1000.0) for x in df.close_time]
	calcVWAP(df, conVal, symbol, quan)
get_bars.counter = 0

def calcVWAP(df, conVal, symb, quan):
	df = df.astype(float)
	df['vwap'] = ((df.v*((df.h+df.l+df.c)/3.00)).cumsum() / df.v.cumsum())
	if((df.iloc[71]['vwap']*1.01)/df.iloc[71]['c'] > 1.01 and conVal != 2):
		subprocess.Popen(["python3", "scanner.py"])
		sys.exit(0)
	if conVal == 0:
		favTrade(df, symb, quan)
	elif conVal == 1:
		findTrade(df, symb, quan)
	elif conVal == 2:
		takeProfit(df, quan, symb)

def favTrade(df, symbol, q):
	if(df.iloc[71]['c'] >= df.iloc[71]['vwap']*1.01):
		side = 1
		lisFor(df, side, symbol, q)
	elif(df.iloc[71]['c'] < df.iloc[71]['vwap']*1.01):
		side = 0
		lisFor(df, side, symbol, q
)
def lisFor(df, side, symbol, q):
	if side == 1:
		print("Price too high (current: " + str(df.iloc[71]['c']) + ", looking for: " + str(df.iloc[71]['vwap']*1.01) + "). Re-scanning... (1 second wait time)")
		time.sleep(1)
		ltcbtc = get_bars(symbol, 0, q)
	elif side == 0:
		print("Favorable setup found. Waiting to cross...")
		ltcbtc = get_bars(symbol, 1, q)
	else:
		print("Error :D")

def findTrade(df, symb, q):
	if(df.iloc[71]['c'] > (df.iloc[71]['vwap']*1.01)):
		print("Crossed VWAP..." + " (" + str(q) + " at " + str(df.iloc[71]['c']) + ")")
		makeTrade(symb, df)
	elif(df.iloc[71]['c'] <= df.iloc[71]['vwap']*1.01):
		print("Price not crossed (" + str(df.iloc[71]['c']) + "vs. " + str(df.iloc[71]['vwap']*1.01) + "). Waiting... (1 second wait time)")
		time.sleep(1)
		ltcbtc = get_bars(symb, 1, q)

def makeTrade(symb, df):
	precision = 8
	price = float(df.iloc[71]['c'])
	price_str = '{:0.0{}f}'.format(price, precision)
	balance = float(client.get_asset_balance(asset='BTC')['free'])
	balance_str = '{:0.0{}f}'.format(balance, precision)
	q = ((float(balance_str) * float(multiplier))/float(price_str))
	print("Quantity: " + str(q))
	print("Price: " + price_str)
	print("Balance: " + balance_str)
	order = client.order_market_buy(
		symbol=symb,
		quantity= int(q)
	)
	global amntBought
	amntBought = int(q)
	print("Amntbought1: " + str(amntBought))
	try:
		# send an email notification to user
		with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
			server.login("xxx", password)
			server.sendmail("xxx", "xxx", "Longed " + str(symb) + " at " + price_str + ".")
	except:
		pass
	print("Purchased")
	quan = int(q)
	takeProfit(df, quan, symb)

def takeProfit(df, q, symb):
	print("Amntbought: " + str(amntBought))
	print("Running take profit...")
	if(df.iloc[71]['c']/(df.iloc[71]['vwap']*1.01) < 1.005):
		stopLoss = df.iloc[71]['vwap']
		print("Current stop loss (1): " + str(stopLoss))
	elif(df.iloc[71]['c']/(df.iloc[71]['vwap']*1.01) >= 1.005 and df.iloc[70]['c']/df.iloc[70]['o'] > 1.015):
		stopLoss = df.iloc[70]['o'] + 0.5 + (df.iloc[70]['c']-df.iloc[70]['o'])/2
		print("Current stop loss (2): " + str(stopLoss))
	elif(df.iloc[71]['c']/(df.iloc[71]['vwap']*1.01) >= 1.005 and df.iloc[70]['c']/df.iloc[70]['o'] <= 1.015):
		stopLoss = df.iloc[70]['o']*0.995
		print("Current stop loss (3): " + str(stopLoss))
	if(df.iloc[71]['c'] <= stopLoss):
		order = client.order_market_sell(
		symbol = symb,
		quantity = int(float(amntBought) * 0.9989)
		)
		print("Sold. Re-starting...")
		precision = 8
		price = float(df.iloc[71]['c'])
		price_str = '{:0.0{}f}'.format(price, precision)
		try:
			with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
				server.login("xxx", password)
				server.sendmail("xxx", "xxx", "Sold " + str(symb) + " at " + price_str + ".")
		except:
			pass
		subprocess.Popen(["python3", "scanner.py"])
		sys.exit(0)
	time.sleep(1)
	get_bars(symb, 2, q)