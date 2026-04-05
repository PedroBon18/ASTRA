import speech_recognition as sr
import pyttsx3
import wikipedia
import pywhatkit
import requests
import json
import time
import base64
from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
import os
import re
from dotenv import load_dotenv
from AppOpener import open as app_open
import pyautogui
import screen_brightness_control as sbc
from ctypes import cast, POINTER
import comtypes
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import winshell
from ddgs import DDGS
import PyPDF2
import psutil

# Importações da ASTRA
from config import OLLAMA_URL, MODEL_NAME, SYSTEM_PROMPT, VISION_MODEL

console = Console()
engine = pyttsx3.init()

# Configuração de Voz
voices = engine.getProperty('voices')
voz_encontrada = False

# 1ª Tentativa: Procura especificamente pela "Maria" (Voz feminina padrão PT-BR)
for voice in voices:
    if "brazil" in voice.name.lower() and "maria" in voice.name.lower():
        engine.setProperty('voice', voice.id)
        voz_encontrada = True
        break

# 2ª Tentativa: Se não achar a Maria, pega qualquer uma em português
if not voz_encontrada:
    for voice in voices:
        if "brazil" in voice.name.lower() or "portuguese" in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break

# Reciclando API´s da Sexta-Feira
load_dotenv()
OPENCAGE_KEY = os.getenv("OPENCAGE_KEY")
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# A Boca
def falar(texto):
    console.print(f"[bold cyan]Astra:[/bold cyan] {texto}")
    engine.say(texto)
    engine.runAndWait()

# Astra o demônio do controle
# Em hipótese alguma altere o código do volume! É gambiarra pura, nem eu mesmo sei como funciona. O Dio Brando morreu por muito menos!
def mudar_volume(nivel):
    try:
        try:
            comtypes.CoInitialize()
        except:
            pass
        
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
ARQUIVO_MEMORIA = "astra_memory.json"
ARQUIVO_LEMBRETES = "astra_reminders.json"

def carregar_memoria():
    try:
        with open(ARQUIVO_MEMORIA, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): # ela ignora se o arquivo estiver corrompido!
        return None

def salvar_memoria(context):
    with open(ARQUIVO_MEMORIA, "w") as f:
        json.dump(context, f)

def agendar_lembrete(tarefa, minutos):
    hora_alvo = datetime.now() + timedelta(minutes=int(minutos))
    lembrete = {
        "tarefa": tarefa,
        "horario": hora_alvo.strftime("%H:%M")
    }
    
    lista = []
    try:
        with open(ARQUIVO_LEMBRETES, "r") as f:
            lista = json.load(f)
    except: pass
    
    lista.append(lembrete)
    with open(ARQUIVO_LEMBRETES, "w") as f:
        json.dump(lista, f)
    
    return f"Ok, vou te lembrar de {tarefa} às {hora_alvo.strftime('%H:%M')}."

def checar_lembretes():
    try:
        with open(ARQUIVO_LEMBRETES, "r") as f:
            lista = json.load(f)
    except: return None

    agora = datetime.now().strftime("%H:%M")
    nova_lista = []
    lembrete_ativo = None

    for item in lista:
        if item["horario"] == agora:
            lembrete_ativo = item["tarefa"]
        else:
            nova_lista.append(item)
    
    if lembrete_ativo:
        with open(ARQUIVO_LEMBRETES, "w") as f:
            json.dump(nova_lista, f)
            
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
    except Exception as e:
        return f"Erro ao escanear o sistema: {e}"

# Reciclando codigo de clima da Sexta-Feira 
def obter_lat_long(cidade):
    url = f"https://api.opencagedata.com/geocode/v1/json?q={cidade}&key={OPENCAGE_KEY}&language=pt&pretty=1"
    try:
        r = requests.get(url).json()
        if r['results']:
            return r['results'][0]['geometry']['lat'], r['results'][0]['geometry']['lng']
    except:
        pass
    return None, None

def obter_clima(cidade):
    lat, lng = obter_lat_long(cidade)
    if not lat: return "Não achei essa cidade."
    
    url = f"{OPEN_METEO_URL}?latitude={lat}&longitude={lng}&current_weather=true&temperature_unit=celsius"
    try:
        r = requests.get(url).json()
        temp = r["current_weather"]["temperature"]
        return f"A temperatura em {cidade} é de {temp} graus."
    except:
        return "Erro ao verificar o clima."
    
def pesquisa_inteligente(termo):
    falar(f"Buscando informações na rede sobre {termo}...")
    try:
        resultados = DDGS().text(termo, region='wt-wt', max_results=5)
        
        if not resultados:
            return "Não encontrei nada na internet sobre isso, senhor."
        
        contexto_web = "Resultados da Web:\n"
        for r in resultados:
            contexto_web += f"- {r['title']}: {r['body']}\n"
        
        prompt = f"""
        <role>Astra</role>
        <directive>
        Sintetize as informações da Web abaixo de forma direta e sem preâmbulos. Se os resumos não falarem sobre o assunto, admita que não encontrou dados suficientes, não invente nada.
        </directive>
        {contexto_web}
        """
        resposta, _ = cerebro_astra(prompt)
        return resposta
        
    except Exception as e:
        console.print(f"[red]Erro na Web:[/red] {e}")
        return "Minha conexão com a rede falhou. A internet pode ter caído ou o provedor cortou nosso acesso."

# O GRANDE SÁBIO (Leitura de PDFs)
def estudar_pdf(nome_arquivo, pergunta_usuario="Faça um resumo dos pontos principais deste documento."):
    # Mapeia o caminho exato para C:\Users\fulano\Documents\PDFs
    pasta_pdfs = os.path.join(winshell.my_documents(), "PDFs")
    
    falar(f"Procurando o PDF '{nome_arquivo}' na sua pasta de Documentos...")
    
    # Se a pasta "PDFs" não existir, a Astra cria ela na hora!
    if not os.path.exists(pasta_pdfs):
        os.makedirs(pasta_pdfs)
        return "A pasta 'PDFs' não existia nos seus Documentos. Acabei de criá-la para você. Mova seus arquivos para lá e me chame de novo."

    caminho_pdf = None

    # Varre apenas a pasta Documents\PDFs
    for arquivo in os.listdir(pasta_pdfs):
        if nome_arquivo in arquivo.lower() and arquivo.endswith('.pdf'):
            caminho_pdf = os.path.join(pasta_pdfs, arquivo)
            break

    if not caminho_pdf:
        return f"Não encontrei nenhum PDF chamado '{nome_arquivo}' na pasta Documentos\\PDFs. Tem certeza de que o nome está certo?"

    falar("Documento encontrado. Absorvendo conhecimento... (Isso pode exigir um pouco da placa de vídeo)")
    
    texto_extraido = ""
    try:
        with open(caminho_pdf, 'rb') as f:
            leitor = PyPDF2.PdfReader(f)
            # Lê as primeiras 5 páginas (Proteção para não fritar minha placa de video)
            limite_paginas = min(len(leitor.pages), 5)
            for i in range(limite_paginas):
                texto_extraido += leitor.pages[i].extract_text() + "\n"
    except Exception as e:
        return f"Erro ao tentar ler o PDF: {e}"

    if not texto_extraido.strip():
        return "O documento parece estar vazio ou é apenas um monte de imagens escaneadas sem texto."

    # Prompt agressivo para o DeepSeek não inventar informações fora do PDF
    prompt = f"""
    <role>Astra</role>
    <directive>
    Responda em Português, seja direto e baseie-se APENAS no texto do documento. Se a resposta não estiver no texto, diga que o documento não menciona isso.
    PEDIDO DO USUÁRIO: {pergunta_usuario}
    </directive>
    <document_text>
    {texto_extraido}
    </document_text>
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
        
        if not r.get("data"):
            return f"Péssimas notícias! A base de dados não tem nenhum registro de '{nome_anime}'."
        
        anime = r["data"][0]
        titulo = anime.get("title", "Desconhecido")
        nota = anime.get("score", "Sem nota")
        eps = anime.get("episodes", "?")
        status = anime.get("status", "Desconhecido")
        sinopse = anime.get("synopsis", "Sem sinopse.")
        
        # Encurralando a Astra no XML do Claude para ela ler os dados como a Mei Hatsume
        prompt = f"""
        <role>Astra</role>
        <directive>
        Você usou sua invenção 'Rastreador Otaku' e puxou os dados abaixo do MyAnimeList. 
        Entregue as informações de forma absurdamente empolgada e orgulhosa do seu bebê (a invenção). 
        Comente sobre a nota (Score), resuma a sinopse e faça uma analogia rápida de otaku.
        </directive>
        <anime_data>
        Título: {titulo}
        Nota: {nota}/10
        Episódios: {eps}
        Status: {status}
        Sinopse Original (Inglês): {sinopse}
        </anime_data>
        """
        resposta, _ = cerebro_astra(prompt)
        return resposta
    except Exception as e:
        return f"O Rastreador Otaku superaqueceu e explodiu! O erro foi: {e}"
    
    # O SENTIDO ARANHA DE HARDWARE (Monitorização psutil)
def relatorio_hardware():
    falar("A ler os sensores internos do nosso lindo bebé...")
    
    cpu_uso = psutil.cpu_percent(interval=1)
    ram_uso = psutil.virtual_memory().percent
    
    # Magia Negra: Descobrir o processo vilão que está a comer a RAM
    processo_fome = "Nenhum"
    max_ram = 0
    for proc in psutil.process_iter(['name', 'memory_percent']):
        try:
            if proc.info['memory_percent'] is not None and proc.info['memory_percent'] > max_ram:
                max_ram = proc.info['memory_percent']
                processo_fome = proc.info['name']
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    # O prompt que injeta a loucura da Mei Hatsume nos dados puros
    prompt = f"""
    <role>Astra</role>
    <directive>
    Você ativou sua invenção 'Sentido Aranha' para verificar a saúde do computador (seu bebê).
    - CPU está em {cpu_uso}% de uso.
    - RAM está em {ram_uso}% de uso.
    - O programa que mais está devorando a memória no momento é o '{processo_fome}' (consumindo {max_ram:.1f}% da RAM sozinho).
    
    Faça um diagnóstico caótico, rápido e cheio de atitude! Se o uso estiver alto, reclame que o '{processo_fome}' está a destruir a nossa obra-prima. Se estiver baixo, comemore o quão eficiente o hardware está rodando.
    </directive>
    """
    resposta, _ = cerebro_astra(prompt)
    return resposta

# FILTRO DE CONSCIÊNCIA (Novo poder para calar a boca do DeepSeek)
def limpar_pensamento(texto):
    """Remove o bloco <think> gerado pelo DeepSeek para a Astra não falar sozinha."""
    return re.sub(r'<think>.*?</think>', '', texto, flags=re.DOTALL).strip()

# O Cérebro da Astra/Ollama
def cerebro_astra(prompt, context=None):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "context": context
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        data = response.json()
        
        novo_contexto = data.get("context")
        salvar_memoria(novo_contexto)
        
        # Filtra a resposta antes de devolver (O segredo do R1:8b)
        resposta_limpa = limpar_pensamento(data["response"])
        return resposta_limpa, novo_contexto 
        
    except Exception as e:
        console.print(f"[red]Erro no cérebro:[/red] {e}")
        return "Estou com dor de cabeça (Erro de conexão).", context
    
# Olho de Agamotto
def analisar_tela(prompt_usuario):
    falar("Analisando a tela... (Um momento)")
    
    caminho_img = "temp_vision.png"
    
    # 1. Print e Tratamento da Imagem
    time.sleep(1.0) 
    pyautogui.screenshot(caminho_img)
    
    if os.path.getsize(caminho_img) < 1000: return "Erro: O print saiu vazio."

    try:
        with open(caminho_img, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode('utf-8')
    except: return "Erro ao processar imagem."
    
    # 2. PASSO A: O Moondream descreve em INGLÊS (Para garantir a precisão)
    payload_visao = {
        "model": VISION_MODEL,
        "prompt": "Describe this image in detail. If there is text, read it.", 
        "stream": False,
        "images": [img_b64]
    }
    
    descricao_ingles = ""
    
    try:
        # TIMEOUT AUMENTADO PARA 180 SEGUNDOS (Para a RTX 2060 não morrer no swap)
        response = requests.post(OLLAMA_URL, json=payload_visao, timeout=180)
        if response.status_code == 200:
            descricao_ingles = response.json()["response"]
            if os.path.exists(caminho_img): os.remove(caminho_img)
        else:
            return f"Erro na visão: {response.status_code}"
    except Exception as e:
        return f"O modelo de visão demorou demais ou falhou: {e}"

    # 3. PASSO B: O DeepSeek traduz para PORTUGUÊS (JACKPOT!)
    prompt_traducao = f"""
    <role>Astra</role>
    <directive>Traduza e interprete a descrição visual abaixo baseando-se na pergunta do usuário.</directive>
    <visual_description>{descricao_ingles}</visual_description>
    <user_question>{prompt_usuario if prompt_usuario else "O que é isso?"}</user_question>
    """

    payload_traducao = {"model": MODEL_NAME, "prompt": prompt_traducao, "stream": False}

    try:
        falar("Processando a imagem com a lógica avançada...")
        response_trad = requests.post(OLLAMA_URL, json=payload_traducao, timeout=180)
        if response_trad.status_code == 200:
            # Filtra o pensamento da tradução também!
            return limpar_pensamento(response_trad.json()["response"])
        else:
            return "Consegui ver (em inglês), mas falhei ao traduzir."
    except:
        return f"Vi isto: {descricao_ingles} (Falha na tradução)"

# LOOP PRINCIPAL HÍBRIDO
def main():
    rec = sr.Recognizer()
    context_chat = carregar_memoria()
    
    console.print(Panel.fit("[bold green]ASTRA: O Demônio Cibernético[/bold green]"))
    
    console.print("[yellow]Escolha o modo de operação:[/yellow]")
    console.print("[1] Modo Voz (Microfone)")
    console.print("[2] Modo Chat (Teclado)")
    modo = input(">> ").strip()
    
    usar_voz = True
    if modo == '2':
        usar_voz = False
        console.print("[green]Modo Chat ativado. Digite seus comandos.[/green]")
    else:
        console.print("[green]Modo Voz ativado. Fale quando quiser.[/green]")

    if context_chat:
        falar("Sistemas online. Memória restaurada.")
    else:
        falar("Sistemas online.")

    while True:
        # Lembretes funcionam nos dois modos
        aviso = checar_lembretes()
        if aviso:
            falar(f"Com licença, senhor. Lembrete: {aviso}")
            time.sleep(1) 

        # As palavras mágicas da Astra agrupadas no lugar certo para evitar Erro de Sintaxe!
        gatilhos_pdf = ['ler pdf', 'estudar documento', 'analisar documento', 'leia o documento', 'leia o pdf', 'analise o pdf', 'analise o documento', 'resuma o documento', 'resumo do pdf']
        gatilhos_visao = ['veja isso', 'analise', 'o que é isso', 'leia isso', 'na minha tela', 'nesta tela', 'descreva a tela', 'que site é esse']
        gatilhos_busca = ['pesquise', 'pesquisar', 'pesquisa', 'busque', 'buscar', 'quem é', 'o que é']
        gatilhos_anime = ['procurar anime', 'buscar anime', 'informações do anime', 'rastrear anime', 'sobre o anime']

        comando = ""

        try:
            # CAPTURA DO COMANDO
            if not usar_voz:
                # MODO TEXTO
                try:
                    comando = input("\n[Você]: ").strip().lower()
                    if not comando: continue 
                except EOFError: break 
            else:
                # MODO VOZ
                with sr.Microphone() as source:
                    console.print("[dim]Ouvindo ambiente... (Ctrl+C para parar)[/dim]")
                    rec.adjust_for_ambient_noise(source)
                    audio = rec.listen(source, timeout=5, phrase_time_limit=5)
                comando = rec.recognize_google(audio, language='pt-BR').lower()
                console.print(f"[yellow]Você disse:[/yellow] {comando}")

            # COMANDOS DE TROCA DE MODO 
            if 'modo chat' in comando or 'modo texto' in comando:
                usar_voz = False
                falar("Entendido. Ativando teclado.")
                continue
            
            elif 'modo voz' in comando or 'modo audio' in comando or 'modo áudio' in comando:
                usar_voz = True
                falar("Entendido. Ativando microfone.")
                continue

            # GATILHO SENTIDO ARANHA (Hardware V0.8.5)
            gatilhos_hardware = ['status do sistema', 'como está o hardware', 'sentido aranha', 'monitorar sistema', 'diagnóstico', 'como está o pc']
            if any(g in comando for g in gatilhos_hardware):
                falar(relatorio_hardware())
                continue
            
            # GATILHO OTAKU (V0.8.3)
            elif any(g in comando for g in gatilhos_anime):
                comando_limpo = comando
                for g in gatilhos_anime:
                    comando_limpo = comando_limpo.replace(g, '')
                comando_limpo = comando_limpo.replace('astra', '').strip()
                
                if not comando_limpo:
                    falar("Qual anime você quer que o Rastreador Otaku localize?")
                    continue
                
                falar(rastreador_otaku(comando_limpo))
                continue

            # GATILHO UNIVERSITÁRIO (V0.9.3 - O Grande Sábio blindado)
            elif any(g in comando for g in gatilhos_pdf):
                comando_limpo = comando
                # Limpa os gatilhos da frase
                for g in gatilhos_pdf:
                    comando_limpo = comando_limpo.replace(g, '')
                
                # Limpa "sujeiras" como a extensão .pdf, vírgulas e a palavra resuma
                comando_limpo = comando_limpo.replace('.pdf', '').replace('e resuma', '').replace('resuma', '').replace('astra', '').replace(',', '').strip()
                
                # Se sobrar nada, é porque você não falou o nome do arquivo
                if not comando_limpo:
                    falar("Qual é o nome do PDF que está na sua pasta de Documentos?")
                    continue
                
                resposta_pdf = estudar_pdf(comando_limpo)
                falar(resposta_pdf)
                continue
            
            # Ativar O Olho de Agamotto (Agora com 180s de timeout)
            elif any(g in comando for g in gatilhos_visao):
                prompt_vision = comando
                for g in gatilhos_visao: # Limpa o comando
                    prompt_vision = prompt_vision.replace(g, '')
                
                resposta_visao = analisar_tela(prompt_vision.strip())
                falar(resposta_visao)
                continue

            # GATILHO DO RADAR Escaneando sem surtar o DeepSeek
            elif 'escanear' in comando or 'mapear' in comando:
                falar(escanear_sistema())
                continue

            # COMANDOS DE HARDWARE 
            elif 'volume' in comando:
                try:
                    numeros = re.findall(r'\d+', comando)
                    if numeros:
                        falar(mudar_volume(int(numeros[0])))
                    elif 'aumentar' in comando or 'sobe' in comando:
                        pyautogui.press('volumeup'); pyautogui.press('volumeup'); falar("Aumentando.")
                    elif 'diminuir' in comando or 'baixar' in comando:
                        pyautogui.press('volumedown'); pyautogui.press('volumedown'); falar("Diminuindo.")
                    elif 'mudo' in comando or 'mutar' in comando:
                        pyautogui.press('volumemute'); falar("Modo silêncio.")
                except Exception as e:
                    falar("Erro ao ajustar volume.")
                continue

            elif 'brilho' in comando:
                try:
                    numeros = [int(s) for s in comando.split() if s.isdigit()]
                    if numeros: falar(mudar_brilho(numeros[0]))
                except: falar("Não entendi o nível de brilho.")
                continue

            elif 'print' in comando or 'captura de tela' in comando: falar(tirar_print()); continue
            elif 'esvaziar lixeira' in comando:
                try: winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=True); falar("Lixeira esvaziada. Adeus, lixo digital.")
                except: falar("A lixeira já está vazia ou deu erro.")
                continue

            elif 'bloquear' in comando and 'pc' in comando: falar("Bloqueando estação de trabalho."); os.system("rundll32.exe user32.dll,LockWorkStation"); continue
            elif 'desligar' in comando and 'pc' in comando: falar("Protocolo de encerramento iniciado. Boa noite, senhor."); os.system("shutdown /s /t 10"); break

            # Comandos especificos Reciclados da Sexta-Feira (Obrigado, meu eu de 26/04/2025! Sempre serei grato. Se inventarem a viagem no tempo para o passado, eu te agradecerei pessoalmente.)
            # melhorando mecanismos de busca da Sexta-Feira (04/04/2026)
            elif 'tocar' in comando or 'toque' in comando:
                musica = comando.replace('tocar', '').replace('toque', '').strip()
                falar(f"Tocando {musica}."); pywhatkit.playonyt(musica); continue
            
            elif 'clima' in comando:
                cidade = comando.replace('clima', '').replace('em', '').replace('de', '').strip()
                falar(obter_clima(cidade)); continue

            elif any(g in comando for g in gatilhos_busca):
                termo = comando
                # Limpa todas as palavras de gatilho para sobrar só o assunto
                for g in gatilhos_busca: termo = termo.replace(g, '')
                # Limpa o nome dela e pontuações
                termo = termo.replace('astra', '').replace(',', '').strip()
                falar(pesquisa_inteligente(termo))
                continue

            elif 'sair' in comando or 'desligar' in comando: falar("Desligando sistemas."); break

            # ASTRA CONTROLADORA! Apartir desse momento ela tem o poder para abrir qualquer APP (ou jogo) dentro do meu computador
            elif 'abrir' in comando:
                nome_app = comando.replace('abrir', '').strip()
                falar(f"Iniciando {nome_app}...")
                
                # 1. Tenta abrir pela memória do "Protocolo Radar" (Para jogos da Steam e atalhos da Área de Trabalho)
                abriu_customizado = False
                try:
                    with open(ARQUIVO_APPS, "r", encoding="utf-8") as f:
                        apps_mapeados = json.load(f)
                    for nome_salvo, caminho in apps_mapeados.items():
                        if nome_app in nome_salvo or nome_salvo in nome_app:
                            os.startfile(caminho) # Comando mágico do Windows que executa qualquer coisa
                            abriu_customizado = True; break
                except: pass # Se o arquivo não existir, segue a vida
                
                # 2. Plano B: Se não estava na Área de Trabalho, usa o AppOpener (Para apps nativos do Windows)
                if not abriu_customizado:
                    try: app_open(nome_app, match_closest=True, output=False) 
                    except: falar(f"Não consegui encontrar o aplicativo {nome_app} no radar.")
                continue

            # Lógica da Astra com Ollama
            else:
                resposta, context_chat = cerebro_astra(comando, context_chat)
                falar(resposta)

        # Tratamento de Silêncio (Necessário para o timeout funcionar e ela checar lembretes)
        except sr.WaitTimeoutError: pass 
        except sr.UnknownValueError: pass 
        except sr.RequestError: falar("Minha audição está fora do ar.")
        except KeyboardInterrupt: break

if __name__ == "__main__":
    main()