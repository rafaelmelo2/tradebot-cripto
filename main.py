import pandas as pd
import os 
import time 
from binance.client import Client
from binance.enums import *
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("API_KEY")
secret_key = os.getenv("SECRET_KEY")

print("Api key ", api_key)
print("Secret key ", secret_key)

cliente_binance = Client(api_key, secret_key)

conta = cliente_binance.get_account()

for ativo in conta["balances"]:
    if ativo["asset"] == 'BTC':
        print(ativo)
    # if float(ativo["free"]) > 0.5:
    #     print(ativo)

# symbol_info = cliente_binance.get_symbol_info('BTCBRL')
# lot_size_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
# min_qty = float(lot_size_filter['minQty'])
# max_qty = float(lot_size_filter['maxQty'])
# step_size = float(lot_size_filter['stepSize'])

# print(lot_size_filter, min_qty, max_qty, step_size)
