import pandas as pd
import os
import time
from binance.client import Client
from dotenv import load_dotenv
import logging

# Configurar o logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Carregar variáveis de ambiente
load_dotenv()

api_key = os.getenv("API_KEY")
secret_key = os.getenv("SECRET_KEY")

cliente_binance = Client(api_key, secret_key)

# Parâmetros de configuração
codigo_operado = "BTCBRL"
ativo_operado = "BTC"
periodo_candle = Client.KLINE_INTERVAL_1HOUR
# periodo_candle = Client.KLINE_INTERVAL_1SECOND
# periodo_candle = Client.KLINE_INTERVAL_1MINUTE
quantidade = 0.015
quantidade_reservada = 1400

# Parâmetros de risco
stop_loss_percentual = 0.02  # 2%
take_profit_percentual = 0.04  # 5%
capital_inicial = 10000  # Para backtests e paper trading


def pegando_dados(codigo, intervalo):
    """Obtém dados históricos do ativo"""
    candles = cliente_binance.get_klines(symbol=codigo, interval=intervalo, limit=1000)
    precos = pd.DataFrame(candles)
    precos.columns = ["tempo_abertura", "abertura", "maxima", "minima", "fechamento", "volume",
                      "tempo_fechamento", "moedas_negociadas", "numero_trades", 
                      "volume_ativo_base_compra", "volume_ativo_cotacao", "-"]
    precos = precos[["fechamento", "tempo_fechamento"]]
    precos["fechamento"] = precos["fechamento"].astype(float)
    precos["tempo_fechamento"] = pd.to_datetime(precos["tempo_fechamento"], unit="ms").dt.tz_localize("UTC")
    precos["tempo_fechamento"] = precos["tempo_fechamento"].dt.tz_convert("America/Sao_Paulo")
    return precos


def estrategia_trade(dados, posicao, preco_entrada):
    """Executa a lógica de trading baseada em médias móveis"""
    dados["media_rapida"] = dados["fechamento"].rolling(window=7).mean()
    dados["media_devagar"] = dados["fechamento"].rolling(window=40).mean()

    ultima_media_rapida = dados["media_rapida"].iloc[-1]
    ultima_media_devagar = dados["media_devagar"].iloc[-1]
    preco_atual = dados["fechamento"].iloc[-1]

    stop_loss = preco_entrada * (1 - stop_loss_percentual) if preco_entrada else None
    take_profit = preco_entrada * (1 + take_profit_percentual) if preco_entrada else None

    if ultima_media_rapida > ultima_media_devagar and not posicao:
        logging.info(f"Compra sinalizada! Preço: {preco_atual}")
        return "COMPRA", preco_atual
    elif ultima_media_rapida < ultima_media_devagar and posicao:
        logging.info(f"Venda sinalizada! Preço: {preco_atual}")
        return "VENDA", preco_atual
    elif posicao and (preco_atual <= stop_loss or preco_atual >= take_profit):
        motivo = "Stop Loss" if preco_atual <= stop_loss else "Take Profit"
        logging.info(f"{motivo} atingido! Preço: {preco_atual}")
        return "VENDA", preco_atual
    return None, preco_entrada


def backtest(dados):
    """Executa backtest da estratégia"""
    capital = capital_inicial
    posicao = False
    preco_entrada = 0
    for i in range(len(dados)):
        dados_slice = dados.iloc[:i+1]
        acao, preco_atual = estrategia_trade(dados_slice, posicao, preco_entrada)
        if acao == "COMPRA":
            preco_entrada = preco_atual
            posicao = True
        elif acao == "VENDA":
            capital += (preco_atual - preco_entrada) * quantidade
            preco_entrada = 0
            posicao = False
    logging.info(f"Capital final após o backtest: {capital:.2f} (lucro: {capital - capital_inicial:.2f})")
    return capital


def paper_trading(dados):
    """Executa paper trading simulando ordens"""
    capital = capital_inicial
    posicao = False
    preco_entrada = 0
    trades = []

    for i in range(len(dados)):
        dados_slice = dados.iloc[:i+1]
        acao, preco_atual = estrategia_trade(dados_slice, posicao, preco_entrada)
        if acao == "COMPRA":
            preco_entrada = preco_atual
            posicao = True
            trades.append({"tipo": "COMPRA", "preco": preco_atual, "capital": capital})
        elif acao == "VENDA":
            lucro = (preco_atual - preco_entrada) * quantidade
            capital += lucro
            preco_entrada = 0
            posicao = False
            trades.append({"tipo": "VENDA", "preco": preco_atual, "lucro": lucro, "capital": capital})

    for trade in trades:
        logging.info(trade)

    logging.info(f"Capital final após paper trading: {capital:.2f}")
    return capital


def simular_tempo_real(codigo, intervalo):
    """
    Simula a estratégia em tempo real usando apenas os dados mais recentes,
    comprando a quantidade mínima possível de BTC de forma dinâmica.
    """
    posicao = False
    preco_entrada = 0
    capital = capital_inicial

    # Definir quantidade mínima de compra (ajuste conforme as regras da Binance)
    quantidade_minima_btc = 0.0001  # Exemplo: 0.0001 BTC

    # Abrir arquivo de log de lucro
    with open("./txt/robo_teste_SimularTempoReal.txt", "w") as arquivo_lucro:
        arquivo_lucro.write("Início do teste em tempo real\n")
        arquivo_lucro.write(f"Capital inicial: {capital:.2f}\n")

    while True:
        try:
            # Obtém os últimos candles do mercado
            candles = cliente_binance.get_klines(symbol=codigo, interval=intervalo, limit=1000)
            precos = pd.DataFrame(candles, columns=["tempo_abertura", "abertura", "maxima", "minima", "fechamento", "volume",
                                                    "tempo_fechamento", "moedas_negociadas", "numero_trades", 
                                                    "volume_ativo_base_compra", "volume_ativo_cotacao", "-"])
            precos["fechamento"] = precos["fechamento"].astype(float)

            # Calcula médias móveis
            media_rapida = precos["fechamento"].iloc[-7:].mean()  # Média rápida (últimos 7 candles)
            media_devagar = precos["fechamento"].iloc[-40:].mean()  # Média devagar (últimos 40 candles)
            preco_atual = precos["fechamento"].iloc[-1]
            horario_atual = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # Obtém horário atual

            logging.info(f"[{horario_atual}] Preço atual: {preco_atual:.2f} | Média Rápida: {media_rapida:.2f} | Média Devagar: {media_devagar:.2f}")

            # Define os limites de risco (se houver posição aberta)
            stop_loss = preco_entrada * (1 - stop_loss_percentual) if preco_entrada else None
            take_profit = preco_entrada * (1 + take_profit_percentual) if preco_entrada else None

            # Calcula a quantidade possível de compra com o capital disponível
            quantidade_compra = max(quantidade_minima_btc, capital // preco_atual)
            if quantidade_compra * preco_atual > capital:
                quantidade_compra = 0  # Caso o capital seja insuficiente para comprar a quantidade mínima

            # Regras de trading
            if media_rapida > media_devagar and not posicao and quantidade_compra > 0:
                logging.info("Sinal de COMPRA detectado.")
                preco_entrada = preco_atual
                posicao = True
                capital -= quantidade_compra * preco_entrada  # Deduz o custo da compra
                logging.info(f"Compra simulada: Preço {preco_entrada:.2f}, Quantidade {quantidade_compra:.6f}, Capital restante {capital:.2f}")

                # Registra no arquivo
                with open("./txt/robo_teste_SimularTempoReal.txt", "a") as arquivo_lucro:
                    arquivo_lucro.write(f"[{horario_atual}] Compra simulada: Preço {preco_entrada:.2f}, Quantidade {quantidade_compra:.6f}, Capital restante {capital:.2f}\n")

            elif media_rapida < media_devagar and posicao:
                lucro = (preco_atual - preco_entrada) * quantidade_compra
                capital += lucro
                logging.info(f"Venda simulada: Preço {preco_atual:.2f}, Lucro {lucro:.2f}, Capital atualizado {capital:.2f}")
                posicao = False
                preco_entrada = 0

                # Registra no arquivo
                with open("./txt/robo_teste_SimularTempoReal.txt", "a") as arquivo_lucro:
                    arquivo_lucro.write(f"[{horario_atual}] Venda simulada: Preço {preco_atual:.2f}, Lucro {lucro:.2f}, Capital atualizado {capital:.2f}\n")

            elif posicao and (preco_atual <= stop_loss or preco_atual >= take_profit):
                motivo = "Stop Loss" if preco_atual <= stop_loss else "Take Profit"
                lucro = (preco_atual - preco_entrada) * quantidade_compra
                capital += lucro
                logging.info(f"{motivo} atingido. Venda simulada: Preço {preco_atual:.2f}, Lucro {lucro:.2f}, Capital atualizado {capital:.2f}")
                posicao = False
                preco_entrada = 0

                # Registra no arquivo
                with open("./txt/robo_teste_SimularTempoReal.txt", "a") as arquivo_lucro:
                    arquivo_lucro.write(f"[{horario_atual}] {motivo}: Preço {preco_atual:.2f}, Lucro {lucro:.2f}, Capital atualizado {capital:.2f}\n")

            # Atualiza patrimônio no arquivo a cada ciclo
            # with open("./txt/robo_teste_SimularTempoReal.txt", "a") as arquivo_lucro:
            #     arquivo_lucro.write(f"[{horario_atual}] Patrimônio atual: {capital:.2f}\n")

            # Aguarda o próximo ciclo
            time.sleep(2)  # Ajuste para teste em tempo real (ex.: 2 segundos)

        except Exception as e:
            logging.error(f"Erro na simulação em tempo real: {str(e)}")
            time.sleep(5)  # Evita reinicializações rápidas em caso de erro








# Execução principal
if __name__ == "__main__":
    modo = input("Escolha o modo de execução ( 1 - backtest/ 2 - paper/ 3 - live/ 4 - tempo real teste): ").strip().lower()
    dados_historicos = pegando_dados(codigo_operado, periodo_candle)

    if modo == "1":
        backtest(dados_historicos)
    elif modo == "2":
        paper_trading(dados_historicos)
    elif modo == "3":
        posicao = False
        preco_entrada = 0
        while True:
            dados_atualizados = pegando_dados(codigo_operado, periodo_candle)
            acao, preco_atual = estrategia_trade(dados_atualizados, posicao, preco_entrada)
            if acao == "COMPRA":
                logging.info("Ordem de compra executada.")
                # Descomentar para ordens reais:
                # cliente_binance.create_order(symbol=codigo_operado, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=quantidade)
                preco_entrada = preco_atual
                posicao = True
            elif acao == "VENDA":
                logging.info("Ordem de venda executada.")
                # Descomentar para ordens reais:
                # cliente_binance.create_order(symbol=codigo_operado, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=quantidade)
                preco_entrada = 0
                posicao = False
            time.sleep(60)  # Aguarda próximo ciclo
    elif modo == "4":
        # Simulação em tempo real
        simular_tempo_real(codigo_operado, periodo_candle)
