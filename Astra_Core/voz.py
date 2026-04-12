import asyncio
import edge_tts
import pygame
from rich.console import Console

console = Console()

# Inicia a "caixa de som" do laboratório
try:
    pygame.mixer.init()
except Exception as e:
    console.print(f"[yellow]Aviso: Não foi possível iniciar o mixer de áudio ({e})[/yellow]")

# O Ficheiro temporário onde a voz será forjada
ARQUIVO_AUDIO = "voz_astra.mp3"

# A Voz da Deusa Cibernética (Herdada do projeto Kobayashi)
VOICE_NAME = "pt-BR-ThalitaNeural" 

async def _gerar_voz_neural(texto):
    """Gera o áudio mp3 utilizando a API da Microsoft."""
    comunicar = edge_tts.Communicate(texto, VOICE_NAME)
    await comunicar.save(ARQUIVO_AUDIO)

# A Nova Boca
def falar(texto):
    console.print(f"[bold cyan]Astra:[/bold cyan] {texto}")
    
    try:
        asyncio.run(_gerar_voz_neural(texto))
        
        # Carrega e liberta a magia acústica!
        pygame.mixer.music.load(ARQUIVO_AUDIO)
        pygame.mixer.music.play()
        
        # Trava a execução do terminal enquanto ela fala, para não atropelar os áudios
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10) # Limita a CPU para não explodir a máquina
            
        pygame.mixer.music.unload()
        
    except Exception as e:
        console.print(f"[bold red]Curto-circuito na caixa de voz:[/bold red] {e}")