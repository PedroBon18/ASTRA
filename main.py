import speech_recognition as sr
import pyttsx3
import wikipedia
import pywhatkit
import requests
import json
import time
from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
import os
from dotenv import load_dotenv
from AppOpener import open as app_open

# Importações da ASTRA
from config import OLLAMA_URL, MODEL_NAME, SYSTEM_PROMPT

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

# # Sistema Anti-Alzaheimer e Lembretes
ARQUIVO_MEMORIA = "astra_memory.json"
ARQUIVO_LEMBRETES = "astra_reminders.json"

def carregar_memoria():
    try:
        with open(ARQUIVO_MEMORIA, "r") as f:
            return json.load(f)
    except FileNotFoundError:
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
        
        return data["response"], novo_contexto 
        
    except Exception as e:
        console.print(f"[red]Erro no cérebro:[/red] {e}")
        return "Estou com dor de cabeça (Erro de conexão).", context

# LOOP PRINCIPAL

def main():
    rec = sr.Recognizer()
    
    # Carrega a memória (Correção da Amnésia da V0.0)
    context_chat = carregar_memoria()
    
    console.print(Panel.fit("[bold green]ASTRA :: SISTEMA INTEGRADO[/bold green]"))
    
    if context_chat:
        falar("Sistemas online. Memória restaurada.")
    else:
        falar("Sistemas online.")

    while True:
        # 2. Checa lembretes antes de ouvir 
        aviso = checar_lembretes()
        if aviso:
            falar(f"Com licença, senhor. Lembrete: {aviso}")
            time.sleep(1) 

        try:
            with sr.Microphone() as source:
                console.print("[dim]Ouvindo ambiente... (Ctrl+C para parar)[/dim]")
                rec.adjust_for_ambient_noise(source)
                
                # O timeout impede que ela fique surda esperando eternamente.
                # Se ninguém falar nada em 5s, ela solta e checa os lembretes de novo.
                audio = rec.listen(source, timeout=5, phrase_time_limit=5)
            
            # Transcrição por Google Speech Recognition - Gratuito (I'm sorry, brother, I'm out of money.)
            comando = rec.recognize_google(audio, language='pt-BR').lower()
            console.print(f"[yellow]Você disse:[/yellow] {comando}")

            # Função Lembretes
            if 'lembre' in comando and 'minutos' in comando:
                try:
                    partes = comando.split()
                    idx_min = partes.index('minutos')
                    tempo = partes[idx_min - 1]
                    tarefa = comando.replace(f"{tempo} minutos", "").replace("me lembre de", "").replace("em", "").strip()
                    resposta = agendar_lembrete(tarefa, tempo)
                    falar(resposta)
                except:
                    falar("Não entendi o tempo. Tente: 'me lembre de X em 10 minutos'.")
                continue

            # Comandos especificos Reciclados da Sexta-Feira (Obrigado, meu eu de 26/04/2025! Sempre serei grato. Se inventarem a viagem no tempo para o passado, eu te agradecerei pessoalmente.)
            elif 'tocar' in comando or 'toque' in comando:
                musica = comando.replace('tocar', '').replace('toque', '').strip()
                falar(f"Tocando {musica}.")
                pywhatkit.playonyt(musica)
                continue
            
            elif 'clima' in comando:
                cidade = comando.replace('clima', '').replace('em', '').replace('de', '').strip()
                relatorio = obter_clima(cidade)
                falar(relatorio)
                continue

            elif 'pesquisar' in comando or 'quem é' in comando:
                termo = comando.replace('pesquisar', '').replace('quem é', '').strip()
                wikipedia.set_lang('pt')
                try:
                    resumo = wikipedia.summary(termo, sentences=2)
                    falar(resumo)
                except:
                    falar("Não encontrei nada na wiki.")
                continue

            elif 'sair' in comando or 'desligar' in comando:
                falar("Desligando sistemas.")
                break

            # ASTRA CONTROLADORA! Apartir desse momento ela tem o poder para abrir qualquer APP (ou jogo) dentro do meu computador
            elif 'abrir' in comando:
                try:
                    
                    nome_app = comando.replace('abrir', '').strip()
                    
                    falar(f"Abrindo {nome_app}...")
                    
                    
                    app_open(nome_app, match_closest=True, output=False) 
                    
                except:
                    falar(f"Não consegui abrir o {nome_app}.")
                continue

            # Lógica da Astra com Ollama
            else:
                resposta, context_chat = cerebro_astra(comando, context_chat)
                falar(resposta)

        # Tratamento de Silêncio (Necessário para o timeout funcionar e ela checar lembretes)
        except sr.WaitTimeoutError:
            pass 
        except sr.UnknownValueError:
            pass 
        except sr.RequestError:
            falar("Minha audição (Google) está fora do ar.")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()