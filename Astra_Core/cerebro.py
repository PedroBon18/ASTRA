import requests
import json
import re
import time
import base64
import os
import pyautogui

from Astra_Core.config import OLLAMA_URL, MODEL_NAME, SYSTEM_PROMPT, VISION_MODEL
from Astra_Core.voz import falar, console

# Sistema Anti-Alzaheimer
ARQUIVO_MEMORIA = "astra_memory.json"

def carregar_memoria():
    try:
        with open(ARQUIVO_MEMORIA, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): # ela ignora se o arquivo estiver corrompido!
        return None

def salvar_memoria(context):
    with open(ARQUIVO_MEMORIA, "w") as f:
        json.dump(context, f)

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
    
# Olho de Agamotto (Lê a tela do PC)
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

# Olho de Agamotto Modificado (Lê arquivos enviados no Discord)
def analisar_imagem_direta(caminho_img, prompt_usuario):
    try:
        with open(caminho_img, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        return f"As minhas lentes não conseguiram focar no arquivo: {e}"
    
    payload_visao = {
        "model": VISION_MODEL,
        "prompt": "Describe this image in detail. If there is text, read it.", 
        "stream": False,
        "images": [img_b64]
    }
    
    descricao_ingles = ""
    try:
        response = requests.post(OLLAMA_URL, json=payload_visao, timeout=180)
        if response.status_code == 200:
            descricao_ingles = response.json()["response"]
        else:
            return f"Erro na visão: {response.status_code}"
    except Exception as e:
        return f"O modelo de visão demorou demais ou falhou: {e}"

    prompt_traducao = f"""
    <role>Astra</role>
    <directive>Traduza e interprete a descrição visual abaixo baseando-se na pergunta do usuário.</directive>
    <visual_description>{descricao_ingles}</visual_description>
    <user_question>{prompt_usuario if prompt_usuario else "O que é isso?"}</user_question>
    """
    payload_traducao = {"model": MODEL_NAME, "prompt": prompt_traducao, "stream": False}

    try:
        response_trad = requests.post(OLLAMA_URL, json=payload_traducao, timeout=180)
        if response_trad.status_code == 200:
            return limpar_pensamento(response_trad.json()["response"])
        else:
            return "Consegui ver (em inglês), mas falhei ao traduzir."
    except:
        return f"Vi isto: {descricao_ingles} (Falha na tradução)"