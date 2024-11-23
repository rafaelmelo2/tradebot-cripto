import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import matplotlib.pyplot as plt

# 1. Carregar os dados
def carregar_dados(caminho_arquivo):
    dados = pd.read_csv(caminho_arquivo, parse_dates=['Date'], index_col='Date')
    dados = dados[['Open', 'High', 'Low', 'Close', 'Volume']]  # Seleciona as colunas relevantes
    return dados

# 2. Pré-processamento
def preprocessar_dados(dados, janela=60):
    scaler = MinMaxScaler(feature_range=(0, 1))
    dados_normalizados = scaler.fit_transform(dados)
    
    X, y = [], []
    for i in range(janela, len(dados_normalizados)):
        X.append(dados_normalizados[i-janela:i])
        y.append(dados_normalizados[i, 3])  # Prevendo o fechamento (Close)
    
    X, y = np.array(X), np.array(y)
    return X, y, scaler

# 3. Criar o modelo LSTM
def criar_modelo(input_shape):
    modelo = Sequential([
        LSTM(units=50, return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(units=50, return_sequences=False),
        Dropout(0.2),
        Dense(units=25),
        Dense(units=1)  # Saída única (previsão do preço de fechamento)
    ])
    modelo.compile(optimizer='adam', loss='mean_squared_error')
    return modelo

# 4. Treinar e Avaliar
def treinar_modelo(modelo, X_train, y_train, X_test, y_test, epochs=50, batch_size=32):
    modelo.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(X_test, y_test), verbose=1)
    return modelo

# 5. Predição e Inversão da Escala
def fazer_predicao(modelo, X, scaler, colunas_originales):
    predicoes = modelo.predict(X)
    escala_invertida = scaler.inverse_transform(np.concatenate((np.zeros((predicoes.shape[0], len(colunas_originales)-1)), predicoes), axis=1))
    return escala_invertida[:, -1]

# 6. Visualizar e Analisar as Previsões
def analisar_predicoes(y_real, y_predito):
    """
    Analisa as previsões em relação aos valores reais.
    Sugere compra/venda baseado na tendência.
    
    Args:
        y_real (np.array): Valores reais do conjunto de teste.
        y_predito (np.array): Valores previstos pelo modelo.
    """
    # Plotando os valores reais e previstos
    plt.figure(figsize=(14, 7))
    plt.plot(y_real, color='blue', label='Preço Real')
    plt.plot(y_predito, color='orange', label='Preço Previsto')
    plt.title('Preço Real vs Previsto')
    plt.xlabel('Tempo')
    plt.ylabel('Preço')
    plt.legend()
    plt.show()

    # Regras simples de compra/venda
    print("\nSugestões de Compra/Venda:")
    for i in range(1, len(y_predito)):
        if y_predito[i] > y_predito[i - 1] and y_predito[i] > y_real[i]:  # Tendência de alta
            print(f"Dia {i}: Sugerido COMPRAR (preço previsto: {y_predito[i]:.2f})")
        elif y_predito[i] < y_predito[i - 1] and y_predito[i] < y_real[i]:  # Tendência de baixa
            print(f"Dia {i}: Sugerido VENDER (preço previsto: {y_predito[i]:.2f})")

# 7. Prever os próximos dias
def prever_futuro(modelo, dados_recentes, scaler, colunas_originales, dias_futuros=5):
    """
    Gera previsões para os próximos dias com base nos últimos valores conhecidos.

    Args:
        modelo (Sequential): Modelo treinado.
        dados_recentes (np.array): Dados recentes usados como entrada para previsões.
        scaler (MinMaxScaler): Escalador usado no pré-processamento.
        colunas_originales (list): Nomes das colunas originais.
        dias_futuros (int): Número de dias a prever.

    Returns:
        list: Lista de preços previstos para os próximos dias.
    """
    previsoes_futuras = []
    entrada_atual = dados_recentes[-1]  # Última janela de entrada conhecida

    for _ in range(dias_futuros):
        entrada_atual = entrada_atual.reshape(1, entrada_atual.shape[0], entrada_atual.shape[1])
        previsao = modelo.predict(entrada_atual)  # Previsão do próximo dia
        previsoes_futuras.append(previsao[0, 0])  # Salvar previsão
        
        # Atualizar a entrada com a previsão feita
        nova_linha = np.concatenate((np.zeros((len(colunas_originales) - 1)), [previsao[0, 0]]))
        nova_linha = scaler.inverse_transform([nova_linha])[0]
        entrada_atual = np.vstack((entrada_atual[0, 1:], nova_linha))

    # Reverter a escala das previsões
    previsoes_futuras = scaler.inverse_transform(
        np.concatenate((np.zeros((len(previsoes_futuras), len(colunas_originales) - 1)), 
                        np.array(previsoes_futuras).reshape(-1, 1)), 
                       axis=1)
    )[:, -1]
    return previsoes_futuras


# Exemplo de uso
if __name__ == "__main__":
    # Caminho para o arquivo de dados CSV
    caminho = 'dados_criptomoeda.csv'
    
    # Carregar e preparar os dados
    dados = carregar_dados(caminho)
    X, y, scaler = preprocessar_dados(dados)
    
    # Dividir em treino e teste
    divisao = int(len(X) * 0.8)
    X_train, X_test = X[:divisao], X[divisao:]
    y_train, y_test = y[:divisao], y[divisao:]
    
    # Criar e treinar o modelo
    modelo = criar_modelo((X_train.shape[1], X_train.shape[2]))
    modelo = treinar_modelo(modelo, X_train, y_train, X_test, y_test)
    

    # 6
    # Fazer previsões
    predicoes = fazer_predicao(modelo, X_test, scaler, dados.columns)
    print(predicoes)

     # Fazer previsões
    predicoes = fazer_predicao(modelo, X_test, scaler, dados.columns)
    
    # Reverter escala dos valores reais para comparação
    y_test_invertido = scaler.inverse_transform(
        np.concatenate((np.zeros((len(y_test), dados.shape[1] - 1)), y_test.reshape(-1, 1)), axis=1)
    )[:, -1]
    
    # Analisar previsões e sugerir ações
    analisar_predicoes(y_test_invertido, predicoes)

    #7
        # Previsões futuras para X dias
    dias_futuros = 5  # Número de dias que deseja prever
    previsoes_futuras = prever_futuro(modelo, X_test, scaler, dados.columns, dias_futuros)

    # Exibir previsões futuras
    print(f"Previsões para os próximos {dias_futuros} dias:")
    for i, valor in enumerate(previsoes_futuras, start=1):
        print(f"Dia {i}: {valor:.2f}")

    # Analisar as previsões em relação a um valor limite
    valor_limite = 50000  # Exemplo: limite para decisão de compra/venda
    for i, valor in enumerate(previsoes_futuras, start=1):
        if valor >= valor_limite:
            print(f"Dia {i}: Sugerido VENDER (previsão: {valor:.2f}, valor limite: {valor_limite})")
        else:
            print(f"Dia {i}: Sugerido MANTER ou COMPRAR (previsão: {valor:.2f})")
