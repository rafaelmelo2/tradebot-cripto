import pandas as pd
import os 
import time 
from binance.client import Client
from binance.enums import *
from dotenv import load_dotenv
from decimal import Decimal

load_dotenv()

# Definindo as chaves da API
api_key = os.getenv("API_KEY")
secret_key = os.getenv("SECRET_KEY")

# Inicializando o cliente da Binance
cliente_binance = Client(api_key, secret_key)

# Definindo parâmetros
codigo_operado = "BTCBRL"
ativo_operado = "BTC"
quantidade_reservada = 1400  # Valor de BRL que deve ter disponível para compra

# Período das candles
periodo = Client.KLINE_INTERVAL_1HOUR

# Definindo moedas
moedas = [
    {"codigo": "BTCBRL", "ativo": "BTC", "quantidade_moeda": 0.00002, "posicao_atual": False},
    {"codigo": "ETHBRL", "ativo": "ETH", "quantidade_moeda": 0.0006, "posicao_atual": False},
    {"codigo": "ADABRL", "ativo": "ADA", "quantidade_moeda": 2, "posicao_atual": False},
    {"codigo": "SOLBRL", "ativo": "SOL", "quantidade_moeda": 0.008, "posicao_atual": False},
    {"codigo": "LINKBRL", "ativo": "LINK", "quantidade_moeda": 0.11, "posicao_atual": False},
    
]

# min_qty = 0.00002  # BTC
# min_qty = 2 # ADA
# min_qty = 0.0006 # eth
# min_qty = 0.008 # SOL

# Pastas de logs
pasta_arquivo_erro = "./txt/r_erros_moedas.txt"
pasta_arquivo_compras_e_vendas = "./txt/r_compra_vendas.txt"
pasta_arquivo_logs_medias = "./txt/r_logs.txt"



# Função para pegar os dados de mercado (candles)
def pegando_dados(codigo, intervalo):
    try:
        candles = cliente_binance.get_klines(symbol=codigo, interval=intervalo, limit=500)
        precos = pd.DataFrame(candles)
        precos.columns = ["tempo_abertura", "abertura", "maxima", "minima", "fechamento", "volume", "tempo_fechamento", "moedas_negociadas", "numero_trades",
                        "volume_ativo_base_compra", "volume_ativo_cotação", "-"]
        precos = precos[["fechamento", "tempo_fechamento"]]
        precos["tempo_fechamento"] = pd.to_datetime(precos["tempo_fechamento"], unit="ms").dt.tz_localize("UTC")
        precos["tempo_fechamento"] = precos["tempo_fechamento"].dt.tz_convert("America/Sao_Paulo")
        return precos
    except Exception as e:
        horario_atual = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"[{horario_atual}] Erro ao pegar dados para {codigo}: {str(e)}")
        with open(pasta_arquivo_erro, "a") as arquivo_erro:
            arquivo_erro.write(f"[{horario_atual}] Erro ao pegar dados para {codigo}: {str(e)}\n")
        return pd.DataFrame()  # Retorna um DataFrame vazio para evitar erros subsequentes


# Função de estratégia de trade
def estrategia_trade(dados, moeda):
    
    try:
        codigo_ativo = moeda["codigo"]
        ativo_operado = moeda["ativo"]
        quantidade_moeda = round(Decimal(moeda["quantidade_moeda"]), 6)
        posicao = moeda["posicao_atual"]
        # print(quantidade_moeda)
        horario_atual = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        dados["media_rapida"] = dados["fechamento"].rolling(window=7).mean()
        dados["media_devagar"] = dados["fechamento"].rolling(window=40).mean()

        
        ultima_media_rapida = dados["media_rapida"].iloc[-1]
        ultima_media_devagar = dados["media_devagar"].iloc[-1]

        print(f"[{ativo_operado}] Última Média Rápida: {ultima_media_rapida} | Última Média Devagar: {ultima_media_devagar}")
        with open(pasta_arquivo_logs_medias, "a") as arquivo_lucro: 
                arquivo_lucro.write(f"[{horario_atual}] [{ativo_operado}] Última Média Rápida: {ultima_media_rapida} | Última Média Devagar: {ultima_media_devagar}\n")


        conta = cliente_binance.get_account()
        quantidade_atual = 0
        pode_comprar = False

        # Verificando os saldos
        for ativo in conta["balances"]:
            if ativo["asset"] == ativo_operado:
                quantidade_atual = float(ativo["free"])
            if ativo["asset"] == 'BRL':
                pode_comprar = float(ativo["free"]) > quantidade_reservada

        # Lógica de compra/venda
        if ultima_media_rapida > ultima_media_devagar and pode_comprar and not posicao:
            order = cliente_binance.create_order(symbol=codigo_ativo, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=quantidade_moeda)
            
            print(f"[{horario_atual}] COMPROU {ativo_operado}!")
            
            moeda["posicao_atual"] = True
            
            price_buy = order['fills'][0]['price']
            with open(pasta_arquivo_compras_e_vendas, "a") as arquivo_lucro: 
                arquivo_lucro.write(f"[{horario_atual}] COMPROU O ATIVO [{ativo_operado}] por: [{price_buy}]\n")

            for ativo in conta["balances"]:
                if ativo["asset"] == 'BRL':
                    with open(pasta_arquivo_compras_e_vendas, "a") as arquivo_lucro:
                        arquivo_lucro.write(f"[{horario_atual}] Após compra [{ativo_operado}]: {ativo['free']}\n")


        elif ultima_media_rapida < ultima_media_devagar and posicao:
            step_size = pegar_quantidade_minima(codigo_ativo)["step_size"]
            quantidade_venda = (quantidade_atual // step_size) * step_size
            order = cliente_binance.create_order(symbol=codigo_ativo, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=quantidade_venda)
            print(f"[{horario_atual}] VENDEU {ativo_operado}!")
            moeda["posicao_atual"] = False

            price_sell = order['fills'][0]['price']
            with open(pasta_arquivo_compras_e_vendas, "a") as arquivo_lucro:
                arquivo_lucro.write(f"[{horario_atual}] VENDEU ATIVO [{ativo_operado}] por: [{price_sell}]\n")
            
            # Verificando saldo após a venda
            for ativo in conta["balances"]:
                if ativo["asset"] == 'BRL':
                    with open(pasta_arquivo_compras_e_vendas, "a") as arquivo_lucro:
                        arquivo_lucro.write(f"[{horario_atual}] Após venda (BRL): {ativo['free']}\n")

        return moeda
    except Exception as e:
        horario_atual = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"[{horario_atual}] Erro na estratégia para {moeda['ativo']}: {str(e)}")
        with open(pasta_arquivo_erro, "a") as arquivo_erro:
            arquivo_erro.write(f"[{horario_atual}] Erro na estratégia para {moeda['ativo']}: {str(e)}\n")
        return moeda


# Função para pegar o valor mínimo de compra e o step_size
def pegar_quantidade_minima(symbol):
    symbol_info = cliente_binance.get_symbol_info(symbol)
    lot_size_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')

    min_qty = Decimal(lot_size_filter['minQty'])
    max_qty = Decimal(lot_size_filter['maxQty'])
    step_size = Decimal(lot_size_filter['stepSize'])

    print(f"Min Qty: {min_qty}, Max Qty: {max_qty}, Step Size: {step_size}")
    
    return min_qty


# # Função para rodar o robô em tempo real
# def rodar_real(codigo_operado, periodo_candle, ativo_operado, quantidade, posicao_atual):
#     if periodo_candle == 1:
#         periodo_candle = Client.KLINE_INTERVAL_1HOUR
#     elif periodo_candle == 2:
#         periodo_candle = Client.KLINE_INTERVAL_1MINUTE
#     elif periodo_candle == 3:
#         periodo_candle = Client.KLINE_INTERVAL_1SECOND
#     else:
#         periodo_candle = Client.KLINE_INTERVAL_1HOUR
    
#     while True:
#         dados_atualizados = pegando_dados(codigo=codigo_operado, intervalo=periodo_candle)
#         posicao_atual = estrategia_trade(dados_atualizados, codigo_ativo=codigo_operado, 
#                                          ativo_operado=ativo_operado, quantidade=quantidade, posicao=posicao_atual)
#         time.sleep(3)


# # Função de menu para iniciar o robô
# def menu_rodar():
#     codigo_operado = input("Código operado (BTCBRL): ").strip().upper()
#     ativo_operado = input("Ativo operado (BTC): ").strip().upper()
#     periodo_candle_pergunta = input("Período candle ( 1 - 1hr/ 2 - 1min/ 3 - 1s/ 0 - SAIR): ").strip().lower()
#     min_qty = pegar_quantidade_minima(codigo_operado)
#     return codigo_operado, ativo_operado, periodo_candle_pergunta, min_qty


def rodar_varias_moedas(moedas, intervalo):
    while True:
        
        for moeda in moedas:
            try:
                dados_atualizados = pegando_dados(moeda["codigo"], intervalo)
                moeda = estrategia_trade(dados_atualizados, moeda)
            except Exception as e:
                horario_atual = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print(f"[{horario_atual}] Erro ao processar {moeda['codigo']}: {str(e)}")
                with open(pasta_arquivo_erro, "a") as arquivo_erro:
                    arquivo_erro.write(f"[{horario_atual}] Erro em {moeda['codigo']}: {str(e)}\n")

            time.sleep(2)  # Pequeno intervalo para evitar sobrecarga na API



# Execução principal
if __name__ == "__main__":
    modo = input("Escolha o modo de execução ( 1 - RODAR / 2 - QTD MINIMA DE COMPRA/ 0 - SAIR): ").strip().lower()
   
    if modo == "0":
        print("Saindo...")
    elif modo == "1":
        horario_atual = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # Obtém horário atual
        # codigo_operado, ativo_operado, periodo_candle, min_qty= menu_rodar()
        # min_qty = 0.00002  # BTC
        # rodar_real(codigo_operado, ativo_operado, periodo_candle, round(Decimal(min_qty), 6), posicao_atual)

        with open("./txt/robo_varias_moedas.txt", "a") as arquivo_lucro:
            arquivo_lucro.write(f"[{horario_atual}] Infos passadas: [{moedas}] \n")
        
        rodar_varias_moedas(moedas, periodo)

    elif modo == "2":
        ativo_pegar_quantidade_minima = input("Codigo do ativo: ").strip().upper()
        print('Quantidade mínima pro ', ativo_pegar_quantidade_minima, pegar_quantidade_minima(ativo_pegar_quantidade_minima))
    else:
        print("Modo inválido, tente novamente.")
