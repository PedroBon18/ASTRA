import discord
import os
import asyncio
import pyautogui
from datetime import datetime
from dotenv import load_dotenv

# Importações internas do laboratório
from Astra_Core.voz import console
from Astra_Core.cerebro import cerebro_astra

load_dotenv()

# Protocolo de Bolso
def iniciar_discord():
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
    
    if not DISCORD_TOKEN or DISCORD_TOKEN == "cole_o_token_gigante_aqui": 
        console.print("[bold red][Discord] ERRO: O Token não foi configurado no arquivo .env![/bold red]")
        return

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        console.print(f"[bold green][Discord]:[/bold green] Astra conectada com sucesso como {client.user}!")

    @client.event
    async def on_message(message):
        if message.author == client.user: return
        if DISCORD_CHANNEL_ID and str(message.channel.id) != DISCORD_CHANNEL_ID: return

        comando = message.content.lower()
        console.print(f"[bold magenta][Discord]:[/bold magenta] {comando}")
        
        # A Invenção Assassina: O Print
        if comando == 'print' or comando == 'tela' or comando == 'ecrã':
            async with message.channel.typing():
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                nome_ficheiro = f"print_discord_{timestamp}.png"
                await asyncio.to_thread(pyautogui.screenshot, nome_ficheiro)
                try:
                    await message.channel.send(file=discord.File(nome_ficheiro))
                    os.remove(nome_ficheiro)
                except Exception as e:
                    await message.channel.send("Minhas lentes embaçaram. Erro ao capturar a tela.")
            return
        
        # O Catálogo de Invenções (Discord)
        if 'gatilhos' in comando or 'suas funções' in comando:
            async with message.channel.typing():
                lista_discord = """
                **🛠️ MANUAL DE INVENÇÕES DA ASTRA 🛠️**
                🤖 `buscar anime [nome]`: Rastreador Otaku (MyAnimeList)
                📚 `ler pdf [nome]`: O Grande Sábio (Lê PDFs locais)
                🕷️ `sentido aranha` ou `status do sistema`: Monitora CPU e RAM
                👁️ `analise a tela` ou `veja isso`: Olho de Agamotto (Visão)
                📡 `escanear`: Mapeia a Área de Trabalho do mestre
                🚀 `abrir [app]`: Inicia um programa no PC
                📸 `print` ou `tela`: Envia um print do PC aqui pro Discord
                🌦️ `clima em [cidade]`: Previsão do tempo
                🎵 `tocar [música]`: Toca a música no YouTube
                🔊 `volume [0-100]` / `brilho [0-100]`: Controle de hardware
                """
                await message.channel.send(lista_discord)
            return

        async with message.channel.typing():
            resposta, _ = await asyncio.to_thread(cerebro_astra, message.content, None)
            for i in range(0, len(resposta), 2000):
                await message.channel.send(resposta[i:i+2000])

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        console.print("[yellow][Discord]: Iniciando ignição dos servidores...[/yellow]")
        client.run(DISCORD_TOKEN)
    except Exception as e:
        console.print(f"[bold red][Discord] O motor explodiu: {e}[/bold red]")