import os
import json
import time
import requests
import pyautogui
import screen_brightness_control as sbc
from ctypes import cast, POINTER
import comtypes
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from datetime import datetime, timedelta
import winshell
from ddgs import DDGS
import PyPDF2
import psutil
from dotenv import load_dotenv
import shutil
from pathlib import Path

# Importações internas do laboratório
from Astra_Core.voz import falar, console
from Astra_Core.cerebro import cerebro_astra


# Reciclando API´s da Sexta-Feira
load_dotenv()
OPENCAGE_KEY = os.getenv("OPENCAGE_KEY")
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# INDIVIDUALIDADE: MESTRE DE ARQUIVOS
def listar_arquivos(diretorio="."):
    # Retorna uma lista organizada para a Astra não se perder
    try:
        itens = os.listdir(diretorio)
        return "\n".join([f"📄 {i}" if os.path.isfile(os.path.join(diretorio, i)) else f"📁 {i}" for i in itens])
    except Exception as e:
        return f"Erro ao vasculhar o setor: {e}"

def modificar_arquivo(caminho, novo_conteudo, modo="w"):
    # "w" para sobrescrever, "a" para adicionar ao final
    try:
        with open(caminho, modo, encoding="utf-8") as f:
            f.write(novo_conteudo)
        return f"Alteração concluída no bebê '{os.path.basename(caminho)}'!"
    except Exception as e:
        return f"Falha na cirurgia do arquivo: {e}"
    
def buscar_arquivo_local(nome_alvo):
    # Para não fritar o PC pesquisando no C: inteiro, vamos focar no ninho do mestre!
    pastas_alvo = [
        winshell.desktop(),
        winshell.my_documents(),
        os.path.join(os.path.expanduser("~"), "Downloads")
    ]
    
    nome_alvo_lower = nome_alvo.lower()
    
    for pasta in pastas_alvo:
        if not os.path.exists(pasta): continue
        
        # O os.walk vai entrar em TODAS as subpastas!
        for raiz, _, arquivos in os.walk(pasta):
            for arquivo in arquivos:
                # Se uma parte do nome bater, é jackpot!
                if nome_alvo_lower in arquivo.lower():
                    caminho_completo = os.path.join(raiz, arquivo)
                    return caminho_completo
                    
    return None

# Astra o demônio do controle
# Em hipótese alguma altere o código do volume! É gambiarra pura, nem eu mesmo sei como funciona. O Dio Brando morreu por muito menos!
def mudar_volume(nivel):
    try:
        try: comtypes.CoInitialize()
        except: pass
        
        device = AudioUtilities.GetSpeakers()
        interface = device.EndpointVolume
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        vol_float = min(max(int(nivel) / 100, 0.0), 1.0)
        volume.SetMasterVolumeLevelScalar(vol_float, None)
        return f"Volume ajustado para {nivel} por cento."
    except Exception as e:
        console.print(f"[red]Erro Volume:[/red] {e}")
        return "Não consegui mexer no som."

def mudar_brilho(nivel):
    try:
        sbc.set_brightness(int(nivel))
        return f"Brilho ajustado para {nivel} por cento. Espero que não fique cego."
    except:
        return "Não consegui controlar o brilho do seu monitor."

def tirar_print():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = f"print_{timestamp}.png"
    pyautogui.screenshot(nome_arquivo)
    return f"Foto da tela capturada: {nome_arquivo}."    

# Sistema Anti-Alzaheimer e Lembretes
ARQUIVO_LEMBRETES = "astra_reminders.json"

def agendar_lembrete(tarefa, minutos):
    hora_alvo = datetime.now() + timedelta(minutes=int(minutos))
    lembrete = {"tarefa": tarefa, "horario": hora_alvo.strftime("%H:%M")}
    lista = []
    try:
        with open(ARQUIVO_LEMBRETES, "r") as f: lista = json.load(f)
    except: pass
    
    lista.append(lembrete)
    with open(ARQUIVO_LEMBRETES, "w") as f: json.dump(lista, f)
    return f"Ok, vou te lembrar de {tarefa} às {hora_alvo.strftime('%H:%M')}."

def checar_lembretes():
    try:
        with open(ARQUIVO_LEMBRETES, "r") as f: lista = json.load(f)
    except: return None

    agora = datetime.now().strftime("%H:%M")
    nova_lista = []
    lembrete_ativo = None

    for item in lista:
        if item["horario"] == agora: lembrete_ativo = item["tarefa"]
        else: nova_lista.append(item)
    
    if lembrete_ativo:
        with open(ARQUIVO_LEMBRETES, "w") as f: json.dump(nova_lista, f)
    return lembrete_ativo

# PROTOCOLO RADAR (Mapeamento de Apps e Jogos)
ARQUIVO_APPS = "astra_apps.json"

def escanear_sistema():
    falar("Iniciando varredura da Área de Trabalho. Buscando executáveis e jogos...")
    desktop = winshell.desktop()
    apps_encontrados = {}
    try:
        for arquivo in os.listdir(desktop):
            if arquivo.endswith(".lnk") or arquivo.endswith(".url"):
                nome_limpo = arquivo.replace(".lnk", "").replace(".url", "").lower().strip()
                caminho_completo = os.path.join(desktop, arquivo)
                apps_encontrados[nome_limpo] = caminho_completo
        with open(ARQUIVO_APPS, "w", encoding="utf-8") as f:
            json.dump(apps_encontrados, f, indent=4)
        return f"Varredura concluída. Mapeei {len(apps_encontrados)} aplicativos na sua Área de Trabalho."
    except Exception as e: return f"Erro ao escanear o sistema: {e}"

# O RADAR DE PROCESSOS 
def radar_de_processos():
    console.print("[bold yellow]Infiltrando no Gestor de Tarefas do computador...[/bold yellow]")
    
    processos_vivos = []
    # pega apenas o que consome mais de 0.5% de RAM
    for proc in psutil.process_iter(['name', 'memory_percent']):
        try:
            mem = proc.info['memory_percent']
            nome = proc.info['name']
            if mem is not None and mem > 0.5:
                processos_vivos.append(f"{nome} ({mem:.1f}% RAM)")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess): 
            pass
    
    # Limpando duplicatas
    processos_unicos = list(set(processos_vivos))
    
    if not processos_unicos:
        lista_proc = "Apenas processos fantasmas e silenciosos do Windows."
    else:
        # Pega os 15 maiores
        lista_proc = "\n".join(processos_unicos[:15]) 
    
# A COLEIRA DE REALIDADE: Instruções muito mais rígidas para o LLM não inventar coisas
    prompt = f"""
    <role>Astra</role>
    <directive>
    Ativaste o 'Radar de Processos' e invadiste o Gestor de Tarefas do mestre.
    Estes são os ÚNICOS programas que estão a correr na máquina agora:
    
    {lista_proc}
    
    REGRAS DE OURO: 
    1. CITE EXPRESSAMENTE os programas reais que você encontrou nessa lista (diga a porcentagem de RAM deles).
    2. NÃO inventes programas que não estão nesta lista! Baseia o teu julgamento ESTRITAMENTE no que lês acima.
    </directive>
    """

    resposta, _ = cerebro_astra(prompt)
    return resposta

# Reciclando codigo de clima da Sexta-Feira 
def obter_lat_long(cidade):
    url = f"https://api.opencagedata.com/geocode/v1/json?q={cidade}&key={OPENCAGE_KEY}&language=pt&pretty=1"
    try:
        r = requests.get(url).json()
        if r['results']: return r['results'][0]['geometry']['lat'], r['results'][0]['geometry']['lng']
    except: pass
    return None, None

def obter_clima(cidade):
    lat, lng = obter_lat_long(cidade)
    if not lat: return "Não achei essa cidade."
    url = f"{OPEN_METEO_URL}?latitude={lat}&longitude={lng}&current_weather=true&temperature_unit=celsius"
    try:
        r = requests.get(url).json()
        temp = r["current_weather"]["temperature"]
        return f"A temperatura em {cidade} é de {temp} graus."
    except: return "Erro ao verificar o clima."
    
def pesquisa_inteligente(termo):
    falar(f"Buscando informações na rede sobre {termo}...")
    try:
        resultados = DDGS().text(termo, region='wt-wt', max_results=5)
        if not resultados: return "Não encontrei nada na internet sobre isso, senhor."
        contexto_web = "Resultados da Web:\n"
        for r in resultados: contexto_web += f"- {r['title']}: {r['body']}\n"
        prompt = f"""
        <role>Astra</role>
        <directive>Sintetize as informações da Web abaixo de forma direta e sem preâmbulos. Se não achar nada, não invente nada.</directive>
        {contexto_web}
        """
        resposta, _ = cerebro_astra(prompt)
        return resposta
    except Exception as e:
        console.print(f"[red]Erro na Web:[/red] {e}")
        return "Minha conexão com a rede falhou. A internet pode ter caído."

# O GRANDE SÁBIO (Leitura de PDFs)
def estudar_pdf(nome_arquivo, pergunta_usuario="Faça um resumo dos pontos principais deste documento."):
    pasta_pdfs = os.path.join(winshell.my_documents(), "PDFs")
    falar(f"Procurando o PDF '{nome_arquivo}' na sua pasta de Documentos...")
    
    if not os.path.exists(pasta_pdfs):
        os.makedirs(pasta_pdfs)
        return "A pasta 'PDFs' não existia nos seus Documentos. Acabei de criá-la para você."

    caminho_pdf = None
    for arquivo in os.listdir(pasta_pdfs):
        if nome_arquivo in arquivo.lower() and arquivo.endswith('.pdf'):
            caminho_pdf = os.path.join(pasta_pdfs, arquivo)
            break

    if not caminho_pdf: return f"Não encontrei nenhum PDF chamado '{nome_arquivo}'."

    falar("Documento encontrado. Absorvendo conhecimento... (Isso pode exigir um pouco da placa de vídeo)")
    texto_extraido = ""
    try:
        with open(caminho_pdf, 'rb') as f:
            leitor = PyPDF2.PdfReader(f)
            limite_paginas = min(len(leitor.pages), 5)
            for i in range(limite_paginas): texto_extraido += leitor.pages[i].extract_text() + "\n"
    except Exception as e: return f"Erro ao tentar ler o PDF: {e}"

    if not texto_extraido.strip(): return "O documento parece estar vazio."

    prompt = f"""
    <role>Astra</role>
    <directive>Responda baseando-se APENAS no texto do documento. PEDIDO DO USUÁRIO: {pergunta_usuario}</directive>
    <document_text>{texto_extraido}</document_text>
    """
    resposta, _ = cerebro_astra(prompt)
    return resposta

# O RASTREADOR OTAKU (Integração Jikan/MyAnimeList) - COM CORREÇÃO DO CLOUDFLARE
def rastreador_otaku(nome_anime):
    falar(f"Ativando o Rastreador Otaku. Colocando '{nome_anime}' na mira...")
    url = f"https://api.jikan.moe/v4/anime?q={nome_anime}&limit=1"
    try:
        # A MÁGICA ESTÁ AQUI: Disfarce de Navegador para enganar o Cloudflare
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(url, headers=headers, timeout=15).json()
        
        if not r.get("data"): return f"Péssimas notícias! A base de dados não tem nenhum registro de '{nome_anime}'."
        
        anime = r["data"][0]
        prompt = f"""
        <role>Astra</role>
        <directive>Você puxou os dados do MyAnimeList. Entregue as informações absurdamente empolgada. Comente a nota e resuma a sinopse.</directive>
        <anime_data>Título: {anime.get("title", "?")}\nNota: {anime.get("score", "?")}/10\nEpisódios: {anime.get("episodes", "?")}\nSinopse: {anime.get("synopsis", "Sem sinopse.")}</anime_data>
        """
        resposta, _ = cerebro_astra(prompt)
        return resposta
    except Exception as e: return f"O Rastreador Otaku superaqueceu e explodiu! O erro foi: {e}"

# O SENTIDO ARANHA DE HARDWARE (Monitorização psutil)
def relatorio_hardware():
    falar("A ler os sensores internos do nosso lindo bebé...")
    cpu_uso = psutil.cpu_percent(interval=1)
    ram_uso = psutil.virtual_memory().percent
    
    # Magia Negra: Descobrir o processo vilão que está comendo a RAM
    processo_fome = "Nenhum"
    max_ram = 0
    for proc in psutil.process_iter(['name', 'memory_percent']):
        try:
            if proc.info['memory_percent'] is not None and proc.info['memory_percent'] > max_ram:
                max_ram = proc.info['memory_percent']
                processo_fome = proc.info['name']
        except: pass
            
    prompt = f"""
    <role>Astra</role>
    <directive>Diagnóstico de hardware: CPU={cpu_uso}%, RAM={ram_uso}%. Maior consumidor: '{processo_fome}' ({max_ram:.1f}%). Faça um diagnóstico caótico!</directive>
    """
    resposta, _ = cerebro_astra(prompt)
    return resposta