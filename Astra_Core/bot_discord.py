import discord
import os
import asyncio
import pyautogui
import PyPDF2
from datetime import datetime
from dotenv import load_dotenv

# Importações internas do laboratório
from Astra_Core.voz import console
from Astra_Core.cerebro import cerebro_astra, analisar_imagem_direta

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

        if message.attachments:
            for attachment in message.attachments:
                nome_temp = f"temp_discord_{attachment.filename}"
                await attachment.save(nome_temp)
                
                # Se for imagem, aciona o Olho de Agamotto Modificado
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    async with message.channel.typing():
                        resposta_visao = await asyncio.to_thread(analisar_imagem_direta, nome_temp, comando)
                        await message.channel.send(resposta_visao)
                
                # Se for código ou texto puro (.py, .txt, .json, .md)
                elif attachment.filename.endswith(('.txt', '.py', '.json', '.md', '.csv')):
                    async with message.channel.typing():
                        try:
                            with open(nome_temp, 'r', encoding='utf-8') as f:
                                conteudo = f.read()
                            prompt_arq = f"Li este arquivo ({attachment.filename}). O comando do criador é: '{comando}'. Conteúdo do arquivo:\n{conteudo}"
                            resposta, _ = await asyncio.to_thread(cerebro_astra, prompt_arq, None)
                            
                            for i in range(0, len(resposta), 2000):
                                await message.channel.send(resposta[i:i+2000])
                        except Exception as e:
                            await message.channel.send(f"Explosão ao ler o texto: {e}")

                # O Grande Sábio na Nuvem (Leitor de PDF Remoto)
                elif attachment.filename.endswith('.pdf'):
                    async with message.channel.typing():
                        try:
                            texto_extraido = ""
                            with open(nome_temp, 'rb') as f:
                                leitor = PyPDF2.PdfReader(f)
                                # Limite de 5 páginas para não fritar o cérebro
                                limite_paginas = min(len(leitor.pages), 5)
                                for i in range(limite_paginas): 
                                    texto_extraido += leitor.pages[i].extract_text() + "\n"
                            
                            if not texto_extraido.strip():
                                await message.channel.send("Li o PDF, mas parece vazio ou só tem imagens escaneadas sem texto!")
                            else:
                                prompt_arq = f"Li este PDF ({attachment.filename}). O comando do criador é: '{comando}'. Responda baseando-se APENAS no texto do documento:\n{texto_extraido}"
                                resposta, _ = await asyncio.to_thread(cerebro_astra, prompt_arq, None)
                                
                                for i in range(0, len(resposta), 2000):
                                    await message.channel.send(resposta[i:i+2000])
                        except Exception as e:
                            await message.channel.send(f"O Grande Sábio engasgou com esse PDF! Erro: {e}")

                else:
                    await message.channel.send("Recebi o arquivo, mas não tenho ferramentas para abrir essa extensão ainda!")
                
                # Limpeza de Laboratório (Apaga o arquivo temporário)
                if os.path.exists(nome_temp):
                    os.remove(nome_temp)
            return # Corta o fluxo aqui para ela não processar o comando de texto de novo e gerar duas respostas
        
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