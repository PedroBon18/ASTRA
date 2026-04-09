import pyttsx3
from rich.console import Console

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

# A Boca
def falar(texto):
    console.print(f"[bold cyan]Astra:[/bold cyan] {texto}")
    engine.say(texto)
    engine.runAndWait()