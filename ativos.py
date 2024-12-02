import pandas as pd
import os 
import time 
from binance.client import Client
from binance.enums import *
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("API_KEY")
secret_key = os.getenv("SECRET_KEY")

# print("Api key ", api_key)
# print("Secret key ", secret_key)

cliente_binance = Client(api_key, secret_key)

conta = cliente_binance.get_account()

moedas = [
    {"codigo": "BTCBRL", "ativo": "BTC", "quantidade_moeda": 0.00002, "posicao_atual": False},
    {"codigo": "ETHBRL", "ativo": "ETH", "quantidade_moeda": 0.0006, "posicao_atual": False},
    {"codigo": "ADABRL", "ativo": "ADA", "quantidade_moeda": 2, "posicao_atual": False},
]

for ativo in conta["balances"]:
    
    for moeda in moedas:
        if moeda["ativo"] == ativo["asset"]:
            print(ativo)
    # if ativo["asset"] == 'BTC':
    #     print(ativo)