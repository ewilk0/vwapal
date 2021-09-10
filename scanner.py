import requests
from bs4 import BeautifulSoup
import ssl, json, urllib
from trades import findSymbols

def scanPairs():
	print("Assembling trade watchlist... (allow up to a minute)")
	page = requests.get("https://www.binance.com/en")
	soup = BeautifulSoup(page.text, "html.parser")
	dct = {
    	"aria-colindex": "2"
	}

	coinPairs = soup.find_all(**dct)
	result = []

	for coin in coinPairs:
		pair = coin.text
		pair = pair.replace("/", "")
		result.append(pair)

	removeFloats(result)

def sigFigCount(input):
	new_input = input.replace(".", "")
	array = list(new_input)
	for char in array:
		if(char != "0"):
			result = len(array) - array.index(char)
			break
		elif(char == "0"):
			pass
	return result

def removeFloats(coinList):
	x = 0
	favPrices = []
	base_url = "https://api.binance.com/api/v3/ticker/price?symbol="
	for coin in coinList:
		if x <= 70:
			response = requests.get(url=base_url+str(coin))
			dict = json.loads(response.text)
			if str(coin) == 'TRXBTC':
				pass
			elif sigFigCount(str(dict["price"])) <= 3:
				favPrices.append(str(coin))
			x += 1
		elif x > 70:
			print("List complete.")
			break

	findSymbols(favPrices, 0, None)

scanPairs()