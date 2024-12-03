import asyncio
from telegram import Bot
import requests
import time

# Substitua pelo token do seu bot
TOKEN_BOT = "7280230861:AAE863iyeJprXRdm69whfubaHhIdCwo-OW8"
CHAT_ID_COMPRA_VENDA = -4703415845  # Substitua pelo ID do grupo
CHAT_ID_ERROS = -4633728358
CHAT_ID_LOGS = -4617414403


mensagem_bot = "Testando!"

bot = Bot(token=TOKEN_BOT)

# Função assíncrona para enviar a mensagem


def pegar_grupos(TOKEN):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

    response = requests.get(url)
    print(response.json())

async def enviar_mensagem(bot, chat_id, msg):
    try:
        await bot.send_message(chat_id=chat_id, text=msg)
        asyncio.sleep(3)
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")


# Executar a função assíncrona
asyncio.run(enviar_mensagem(bot, CHAT_ID_COMPRA_VENDA, mensagem_bot))
asyncio.run(enviar_mensagem(bot, CHAT_ID_ERROS,mensagem_bot))
asyncio.run(enviar_mensagem(bot, CHAT_ID_LOGS,mensagem_bot))
# asyncio.sleep(3)
# pegar_grupos(TOKEN_BOT)
