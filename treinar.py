import requests
import pandas as pd
import os

def obter_dados_criptomoeda(par="BTCUSDT", intervalo="1d", limite=500):
    """
    Obtém dados históricos de uma criptomoeda usando a API da Binance.
    
    Args:
        par (str): Par de negociação (ex.: "BTCUSDT").
        intervalo (str): Intervalo dos candles (ex.: "1d" para diário).
        limite (int): Quantidade de registros a buscar (máx: 1000).
    
    Returns:
        pd.DataFrame: Dados no formato de DataFrame.
    """
    url = f"https://api.binance.com/api/v3/klines"
    params = {
        "symbol": par,
        "interval": intervalo,
        "limit": limite
    }
    
    # Fazendo a requisição
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Erro ao obter dados da API: {response.json()}")
    
    # Processando os dados
    dados = response.json()
    colunas = [
        "Date", "Open", "High", "Low", "Close", "Volume",
        "CloseTime", "QuoteAssetVolume", "Trades",
        "TakerBaseVolume", "TakerQuoteVolume", "Ignore"
    ]
    df = pd.DataFrame(dados, columns=colunas)
    
    # Convertendo os timestamps para datas legíveis
    df["Date"] = pd.to_datetime(df["Date"], unit="ms")
    df.set_index("Date", inplace=True)
    
    # Mantendo apenas as colunas relevantes
    df = df[["Open", "High", "Low", "Close", "Volume", 
            "CloseTime", "QuoteAssetVolume", "Trades",
            "TakerBaseVolume", "TakerQuoteVolume", "Ignore"]]
    df = df.astype(float)  # Converte valores para float
    return df

def salvar_dados_csv(df, caminho="dados_criptomoeda.csv"):
    """
    Salva os dados em um arquivo CSV.
    
    Args:
        df (pd.DataFrame): Dados a serem salvos.
        caminho (str): Caminho do arquivo CSV.
    """
    df.to_csv(caminho)
    print(f"Dados salvos em: {caminho}")

if __name__ == "__main__":
    # Obter dados da Binance
    print("Obtendo dados da criptomoeda...")
    dados = obter_dados_criptomoeda(par="BTCUSDT", intervalo="1d", limite=500)
    
    # Salvar os dados em um arquivo CSV
    salvar_dados_csv(dados)
