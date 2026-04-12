import discord
import os
import asyncio
import pyautogui
import PyPDF2
import json
from datetime import datetime
from dotenv import load_dotenv



# Importações internas do laboratório
from Astra_Core.voz import console
from Astra_Core.cerebro import cerebro_astra, analisar_imagem_direta
from Astra_Core.voz import console
from Astra_Core.cerebro import cerebro_astra, analisar_imagem_direta
from AppOpener import open as app_open, close as app_close
from Astra_Core.ferramentas import radar_de_processos, ARQUIVO_APPS, buscar_arquivo_local
from Astra_Core.ferramentas import radar_de_processos, ARQUIVO_APPS

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
        
        # O Cão Farejador (Busca e Envio de Arquivos)
        gatilhos_arquivos = ['me mande o arquivo', 'enviar arquivo', 'procure o arquivo', 'mande o arquivo']
        if any(g in comando for g in gatilhos_arquivos):
            for g in gatilhos_arquivos:
                if g in comando:
                    nome_arquivo = comando.replace(g, '').strip()
                    break
            
            async with message.channel.typing():
                await message.channel.send(f"Ativando o Cão Farejador! Vasculhando a sua Área de Trabalho, Documentos e Downloads atrás de '{nome_arquivo}'...")
                
                # Joga a busca pesada para uma thread separada para não travar a Astra
                caminho_encontrado = await asyncio.to_thread(buscar_arquivo_local, nome_arquivo)
                
                if caminho_encontrado:
                    # Trava de Segurança: Verifica o tamanho do arquivo
                    tamanho_mb = os.path.getsize(caminho_encontrado) / (1024 * 1024)
                    if tamanho_mb > 25:
                        await message.channel.send(f"Achei o bebê! Mas ele é muito gordo ({tamanho_mb:.1f} MB)! O limite do Discord é 25MB. Vou precisar de uma dieta compressora primeiro!")
                    else:
                        await message.channel.send(f"Alvo localizado! Extraindo e enviando o bebê: `{os.path.basename(caminho_encontrado)}` 💥", file=discord.File(caminho_encontrado))
                else:
                    await message.channel.send(f"Vasculhei as zonas principais, mas não achei nenhum vestígio desse bebê. Tem certeza que o nome está certo ou que ele não está escondido em outro HD?")
            return
        # --------------------------------------------------
        
        
        gatilhos_processos = ['processos abertos', 'programas abertos', 'o que está rodando', 'gerenciador de tarefas']
        if any(g in comando for g in gatilhos_processos):
            async with message.channel.typing():
                # Executa a ferramenta e manda a resposta real pro Discord
                resposta = await asyncio.to_thread(radar_de_processos)
                for i in range(0, len(resposta), 2000):
                    await message.channel.send(resposta[i:i+2000])
            return
        
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
                📚 `ler pdf [nome]`: O Grande Sábio (Lê PDFs/TXT/Arquivos Remotos)
                🕷️ `sentido aranha` ou `status do sistema`: Monitora CPU e RAM
                📋 `processos abertos` ou `programas abertos`: Radar de Processos (Gerenciador de Tarefas)
                👁️ `analise a tela` ou `veja isso`: Olho de Agamotto (Lê Tela/Imagens)
                📡 `escanear`: Mapeia a Área de Trabalho do mestre
                🚀 `abrir [app]`: Inicia um programa no PC
                ❌ `fechar [app]`: Encerra um programa rodando no PC
                📸 `print` ou `tela`: Envia um print do PC aqui pro Discord
                🌦️ `clima em [cidade]`: Previsão do tempo
                🎵 `tocar [música]`: Toca a música no YouTube
                🔊 `volume [0-100]` / `brilho [0-100]`: Controle de hardware
                """
                await message.channel.send(lista_discord)
            return

        # Controle Remoto de Vida e Morte (Abrir/Fechar Apps)
        if 'abrir' in comando:
            nome_app = comando.replace('abrir', '').strip()
            async with message.channel.typing():
                abriu = False
                try:
                    # 1ª Tentativa: Tenta abrir pelos atalhos hackeados do nosso Radar
                    with open(ARQUIVO_APPS, "r", encoding="utf-8") as f:
                        for nome, caminho in json.load(f).items():
                            if nome_app in nome: 
                                os.startfile(caminho)
                                abriu = True
                                await message.channel.send(f"Ignição ativada! Iniciando {nome_app} no PC do mestre...")
                                break
                except: pass
                
                # 2ª Tentativa: Tenta abrir pelo AppOpener nativo do Windows
                if not abriu:
                    try: 
                        await asyncio.to_thread(app_open, nome_app, match_closest=True, output=False) 
                        await message.channel.send(f"Ignição ativada! Iniciando {nome_app} no PC do mestre...")
                    except: 
                        await message.channel.send("App não encontrado nas minhas lentes. Tem certeza que esse bebê existe?")
            return

        if 'fechar' in comando:
            nome_app = comando.replace('fechar', '').strip()
            async with message.channel.typing():
                await message.channel.send(f"Ativando protocolo de aniquilação remota para {nome_app}...")
                try: 
                    # Dispara o AppOpener em segundo plano para matar o processo
                    await asyncio.to_thread(app_close, nome_app, match_closest=True, output=False)
                    await message.channel.send(f"BUM! 💥 {nome_app} foi explodido e removido da RAM da sua máquina!")
                except: 
                    await message.channel.send("As minhas lentes não acharam esse bebê rodando. Ele já deve estar morto.")
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