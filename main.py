import speech_recognition as sr
import pyttsx3
import wikipedia
import pywhatkit
import requests
from rich.console import Console
from rich.panel import Panel
import os
from dotenv import load_dotenv

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
        return data["response"], data.get("context")
    except Exception as e:
        console.print(f"[red]Erro no cérebro:[/red] {e}")
        return "Estou com dor de cabeça (Erro de conexão).", context

# LOOP PRINCIPAL
def main():
    rec = sr.Recognizer()
    context_chat = None # Memória da conversa
    
    console.print(Panel.fit("[bold green]ASTRA :: SISTEMA INTEGRADO[/bold green]"))
    falar("Sistemas online. O que deseja, senhor?")

    while True:
        try:
            with sr.Microphone() as source:
                console.print("[dim]Ouvindo ambiente...[/dim]")
                rec.adjust_for_ambient_noise(source)
                audio = rec.listen(source)
            
            # Transcrição por Google Speech Recognition - Gratuito (I'm sorry, brother, I'm out of money.)
            comando = rec.recognize_google(audio, language='pt-BR').lower()
            console.print(f"[yellow]Você disse:[/yellow] {comando}")

            # Comandos especificos Reciclados da Sexta-Feira (Obrigado meu eu de 26/04/2025! eu sempre serei grato. se inventarem a viagem no tem para o passado eu te agradecerei pessoalmente)
            if 'tocar' in comando or 'toque' in comando:
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

            # Lógica "Astra" com Ollama
            # Se não for um comando específico, o Astra "pensa" e responde
            else:
                resposta, context_chat = cerebro_astra(comando, context_chat)
                falar(resposta)

        except sr.UnknownValueError:
            pass # Não entendeu nada, ignora
        except sr.RequestError:
            falar("Minha audição (Google) está fora do ar.")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()