import pandas as pd
import os 
import time 
from binance.client import Client
from binance.enums import *
from dotenv import load_dotenv
from decimal import Decimal






# Definindo as chaves da API
#---------------------------------------------------------
load_dotenv()
api_key = os.getenv("API_KEY")
secret_key = os.getenv("SECRET_KEY")
#---------------------------------------------------------


# TESTE FUTURO TELEGRAM
#---------------------------------------------------------
# import asyncio
# from telegram import Bot
#
# token_bot = os.getenv("TOKEN_BOT")
# chat_id_compra_venda = os.getenv("CHAT_ID_COMPRA_VENDA")
# chat_id_erros = os.getenv("CHAT_ID_ERROS")
# chat_id_logs = os.getenv("CHAT_ID_LOGS")
# bot = Bot(token=token_bot)
#---------------------------------------------------------

# Inicializando o cliente da Binance
#--------------------------------------------
cliente_binance = Client(api_key, secret_key)
#--------------------------------------------

# PARÂMETROS INICIALIZAÇÃO
#------------------------------------------------------------------------------
quantidade_reservada = 1350  # Valor de BRL que deve ter disponível para compra

    # MEDIAS MOVEIS
media_movel_rapida = 7
media_movel_lenta = 40
#------------------------------------------------------------------------------


# Período das candles
periodo = Client.KLINE_INTERVAL_1HOUR

# DEFININDO MOEDAS A SER NEGOCIADA
# codigo                    : CODIGO A SER NEGOCIADO (BTCBRL)
# ativo                     : ATIVO A SER NEGOCIADO  (BTC)
# quantidade_moeda          : QTD MINIMA A SER NEGOCIADA ALCANÇANDO OS 10 REAIS
# posicao_atual             : True -> comprado; False -> vendido
# quantidade_minima_moeda   : QTD MINIMA PRA VERIFICAR SE ESTÁ COMPRADO
#-----------------------------------------------------------------------------------------------------------------------------------
moedas = [
    {"codigo": "BTCBRL", "ativo": "BTC", "quantidade_moeda": 0.00002, "posicao_atual": True, "quantidade_minima_moeda": 0.00001},
    {"codigo": "ETHBRL", "ativo": "ETH", "quantidade_moeda": 0.0006, "posicao_atual": True, "quantidade_minima_moeda": 0.0005},
    {"codigo": "ADABRL", "ativo": "ADA", "quantidade_moeda": 2, "posicao_atual": True, "quantidade_minima_moeda": 1.5},
    {"codigo": "SOLBRL", "ativo": "SOL", "quantidade_moeda": 0.009, "posicao_atual": True, "quantidade_minima_moeda": 0.008},
    {"codigo": "LINKBRL", "ativo": "LINK", "quantidade_moeda": 0.11, "posicao_atual": True, "quantidade_minima_moeda": 0.09},
]
#-----------------------------------------------------------------------------------------------------------------------------------

# PASTAS DE LOGS
#-----------------------------------------------------------
pasta_arquivo_erro = "./txt/r_erros_moedas.txt"                 # LOGS DE ERROS
pasta_arquivo_compras_e_vendas = "./txt/r_compra_vendas.txt"    # COMPRAS E VENDAS
pasta_arquivo_logs_medias = "./txt/r_logs.txt"                  # LOGS DAS MEDIAS
pasta_arquivo_infos_iniciadas = "./txt/r_infos_iniciadas.txt"   # INICIALIZAÇÕES DE CÓDIGO
#-----------------------------------------------------------

# INICIALIZANDO BINANCE
#------------------------------------
conta = cliente_binance.get_account()
#------------------------------------

# FUNÇÃO PARA LOGS
#----------------------------------------------
def log(caminho_arquivo, mensagem):
    with open(caminho_arquivo, "a") as arquivo:
        arquivo.write(f"{mensagem}")
#----------------------------------------------


# FUNÇÃO PARA INICIAR O PROGRAMA E VERIFICAR SE ESTÁ COMPRADO OU VENDIDO CADA MOEDA
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------
def verifica_moedas():
    for moeda in moedas:
        try:
            for ativo in conta["balances"]:
                if ativo["asset"] == moeda["ativo"]:
                    
                    # SE A QTD POSSUIDA FOR MAIOR QUE A QTD MINIMA O ATIVO FICA COMO COMPRADO
                    #-------------------------------------------------------------------------------------------------------------------------------------------
                    if float(ativo["free"]) > moeda["quantidade_minima_moeda"]:
                        moeda["posicao_atual"] = True
                        log(pasta_arquivo_infos_iniciadas, f"[{moeda['codigo']}]: QtdDisponivel: [{ativo["free"]}] logo posição: [{moeda["posicao_atual"]}] \n")

                    else:
                        moeda["posicao_atual"] = False
                        log(pasta_arquivo_infos_iniciadas, f"[{moeda['codigo']}]: QtdDisponivel: [{ativo["free"]}] logo posição: [{moeda["posicao_atual"]}] \n")
                    #-------------------------------------------------------------------------------------------------------------------------------------------

        except Exception as e:
            horario_atual = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print(f"[{horario_atual}] Erro ao processar {moeda['codigo']}: {str(e)}")
            log(pasta_arquivo_erro, f"[{horario_atual}] Erro em {moeda['codigo']}: {str(e)}\n")
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------            

# Função para pegar os dados de mercado (candles)
#-------------------------------------------------------------------------------------------------------------------------------------------------------------
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
        log(pasta_arquivo_erro, f"[{horario_atual}] Erro ao pegar dados para {codigo}: {str(e)}\n")

        return pd.DataFrame()  # Retorna um DataFrame vazio para evitar erros subsequentes
#-------------------------------------------------------------------------------------------------------------------------------------------------------------


# Função de estratégia de trade
def estrategia_trade(dados, moeda):
    try:
        # PEGAR MOEDA E SEUS ATRIBUTOS
        #----------------------------------------------------------------------
        codigo_ativo = moeda["codigo"]
        ativo_operado = moeda["ativo"]
        quantidade_moeda = round(Decimal(moeda["quantidade_moeda"]),8)
        posicao = moeda["posicao_atual"]
        #----------------------------------------------------------------------

        # PEGAR MEDIAS MOVEIS DOS DADOS ANTIGOS
        #------------------------------------------------------------------------------------
        horario_atual = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        dados["media_rapida"] = dados["fechamento"].rolling(window=media_movel_rapida).mean()
        dados["media_devagar"] = dados["fechamento"].rolling(window=media_movel_lenta).mean()
        
        ultima_media_rapida = dados["media_rapida"].iloc[-1]
        ultima_media_devagar = dados["media_devagar"].iloc[-1]
        #------------------------------------------------------------------------------------


        # IMPRIMIR AS MÉDIAS
        #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
        print(f"[{ativo_operado}] Última Média Rápida: {ultima_media_rapida} | Última Média Devagar: {ultima_media_devagar}")
        log(pasta_arquivo_logs_medias, f"[{horario_atual}] [{ativo_operado}] Última Média Rápida: {ultima_media_rapida} | Última Média Devagar: {ultima_media_devagar}\n")
        #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
        
        # VARIÁVEIS ALEATÓRIAS NECESSÁRIAS
        #---------------------------------
        quantidade_atual = 0
        pode_comprar = False
        #---------------------------------

        # VERIFICANDO SALDO SE É POSSÍVEL COMPRAR MAIS OU NÃO
        # VERIFICANDO A QUANTIDADE ATUAL DE ATIVOS DA MOEDA PASSADA
        #------------------------------------------------------
        for ativo in conta["balances"]:
            if ativo["asset"] == ativo_operado:
                quantidade_atual = Decimal(ativo["free"])
            if ativo["asset"] == 'BRL':
                if float(ativo["free"]) > quantidade_reservada:
                    pode_comprar = True
                else:
                    pode_comprar = False
        #------------------------------------------------------

        # LOGICA DE COMPRA
        #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
        if ultima_media_rapida > ultima_media_devagar and pode_comprar and not posicao:
            print(quantidade_moeda)
            order = cliente_binance.create_order(symbol=codigo_ativo, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=quantidade_moeda)
            
            print(f"[{horario_atual}] COMPROU {ativo_operado}!")
            
            moeda["posicao_atual"] = True
            
            log(pasta_arquivo_compras_e_vendas,f"[{horario_atual}] COMPROU O ATIVO [{ativo_operado}]\n")

            for ativo in conta["balances"]:
                if ativo["asset"] == 'BRL':
                    log(pasta_arquivo_compras_e_vendas, f"[{horario_atual}] Após compra [{ativo_operado}]: {ativo['free']}\n")
        #-----------------------------------------------------------------------------------------------------------------------------------------------------------------

        # LOGICA DE VENDA
        #-----------------------------------------------------------------------------------------------------------------------------------------------------------------
        elif ultima_media_rapida < ultima_media_devagar and posicao:

            symbol_info = cliente_binance.get_symbol_info(codigo_ativo)
            step_size = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')['stepSize']
            quantidade_venda = round(Decimal(ajustar_quantidade_para_lote(quantidade_atual * Decimal(0.99), step_size)),8)
            print('quantidade_venda', quantidade_venda)

            order = cliente_binance.create_order(symbol=codigo_ativo, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=quantidade_venda)
            print(f"[{horario_atual}] VENDEU {ativo_operado}!")
            moeda["posicao_atual"] = False

            log(pasta_arquivo_compras_e_vendas, f"[{horario_atual}] VENDEU ATIVO [{ativo_operado}]\n")


            # Verificando saldo após a venda
            for ativo in conta["balances"]:
                if ativo["asset"] == 'BRL':
                    log(pasta_arquivo_compras_e_vendas, f"[{horario_atual}] Após venda (BRL): {ativo['free']}\n")
        #-----------------------------------------------------------------------------------------------------------------------------------------------------------------

        return moeda
    
    except Exception as e:
        horario_atual = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"[{horario_atual}] Erro na estratégia para {moeda['ativo']}: {str(e)}")
        log(pasta_arquivo_erro, f"[{horario_atual}] Erro na estratégia para {moeda['ativo']}: {str(e)}\n")
        return moeda

# AJUSTAR QUANTIDADE DE MOEDA PRA VENDA - linha 205
#----------------------------------------------------------------
def ajustar_quantidade_para_lote(quantidade, step_size):
    """
    Ajusta a quantidade para ser um múltiplo válido de step_size.
    """
    step_size = Decimal(step_size)
    quantidade_ajustada = (quantidade // step_size) * step_size
    return float(quantidade_ajustada)
#----------------------------------------------------------------

# Função para pegar o valor mínimo de compra
#---------------------------------------------------------------------------------------------
def pegar_quantidade_minima(symbol):
    symbol_info = cliente_binance.get_symbol_info(symbol)
    lot_size_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')

    min_qty = Decimal(lot_size_filter['minQty'])
    max_qty = Decimal(lot_size_filter['maxQty'])
    step_size = Decimal(lot_size_filter['stepSize'])

    print(f"Min Qty: {min_qty}, Max Qty: {max_qty}, Step Size: {step_size}")
    
    return min_qty
#---------------------------------------------------------------------------------------------


# FUNÇÃO PRA RODAR A LISTA DE MOEDAS COM O INTERVALO PRÉ-DEFINIDO
#---------------------------------------------------------------------------------------------------
def rodar_varias_moedas(moedas, intervalo):
    while True:
        
        for moeda in moedas:
            try:
                dados_atualizados = pegando_dados(moeda["codigo"], intervalo)
                moeda = estrategia_trade(dados_atualizados, moeda)
            except Exception as e:
                horario_atual = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print(f"[{horario_atual}] Erro ao processar {moeda['codigo']}: {str(e)}")
                log(pasta_arquivo_erro, f"[{horario_atual}] Erro em {moeda['codigo']}: {str(e)}\n")
            time.sleep(2)  # Pequeno intervalo para evitar sobrecarga na API
#---------------------------------------------------------------------------------------------------


# Execução principal
#------------------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    modo = input("Escolha o modo de execução ( 1 - RODAR / 2 - QTD MINIMA DE COMPRA/ 0 - SAIR): ").strip().lower()
   
    if modo == "0":
        print("Saindo...")
    elif modo == "1":
        horario_atual = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # Obtém horário atual
        log(pasta_arquivo_infos_iniciadas, f"[{horario_atual}] --------- NOVA EXECUÇÃO Infos passadas: [{moedas}] ---------\n")

        verifica_moedas()

        rodar_varias_moedas(moedas, periodo)

    elif modo == "2":
        ativo_pegar_quantidade_minima = input("Codigo do ativo: ").strip().upper()
        print('Quantidade mínima pro ', ativo_pegar_quantidade_minima, pegar_quantidade_minima(ativo_pegar_quantidade_minima))
    else:
        print("Modo inválido, tente novamente.")
#------------------------------------------------------------------------------------------------------------------------------
