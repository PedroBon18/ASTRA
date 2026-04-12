import speech_recognition as sr
import threading
import time
import os
import re
import json
import pywhatkit
from rich.panel import Panel
from AppOpener import open as app_open
import winshell
import pyautogui

# Importando os órgãos do laboratório!
from Astra_Core.voz import falar, console
from Astra_Core.cerebro import carregar_memoria, cerebro_astra, analisar_tela
from Astra_Core.bot_discord import iniciar_discord
from AppOpener import open as app_open, close as app_close
from Astra_Core.ferramentas import (
    checar_lembretes, mudar_volume, mudar_brilho, tirar_print,
    escanear_sistema, obter_clima, pesquisa_inteligente,
    estudar_pdf, rastreador_otaku, relatorio_hardware, ARQUIVO_APPS,
    radar_de_processos
)

# LOOP PRINCIPAL HÍBRIDO
def main():
    rec = sr.Recognizer()
    context_chat = carregar_memoria()

    # Liga a Antena do Discord
    discord_thread = threading.Thread(target=iniciar_discord, daemon=True)
    discord_thread.start()
    # PROTOCOLO INSÔNIA: Proíbe o Windows de dormir!
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
        console.print("[bold blue][Sistema]: Protocolo Insônia ativado. O PC permanecerá acordado![/bold blue]")
    except Exception as e: console.print(f"[bold red]Falha no Protocolo Insônia:[/bold red] {e}")
    
    console.print(Panel.fit("[bold green]ASTRA: O Demônio Cibernético[/bold green]"))
    console.print("[yellow]Escolha o modo:[/yellow]\n[1] Modo Voz\n[2] Modo Chat")
    modo = input(">> ").strip()
    
    usar_voz = False if modo == '2' else True
    console.print(f"[green]Modo {'Chat' if not usar_voz else 'Voz'} ativado.[/green]")
    falar("Sistemas online. Memória restaurada." if context_chat else "Sistemas online.")

    while True:
        aviso = checar_lembretes()
        if aviso: falar(f"Com licença, senhor. Lembrete: {aviso}"); time.sleep(1) 

        # As palavras mágicas da Astra agrupadas no lugar certo para evitar Erro de Sintaxe!
        gatilhos_pdf = ['ler pdf', 'estudar documento', 'analisar documento']
        gatilhos_visao = ['veja isso', 'analise', 'o que é isso', 'na minha tela', 'descreva a tela']
        gatilhos_busca = ['pesquise', 'pesquisar', 'busque', 'quem é', 'o que é']
        gatilhos_anime = ['procurar anime', 'buscar anime', 'rastrear anime']
        gatilhos_hardware = ['status do sistema', 'como está o hardware', 'sentido aranha']
        gatilhos_processos = ['processos abertos', 'programas abertos', 'o que está rodando', 'gerenciador de tarefas']

        comando = ""
        try:
            if not usar_voz:
                try:
                    comando = input("\n[Você]: ").strip().lower()
                    if not comando: continue 
                except EOFError: break 
            else:
                with sr.Microphone() as source:
                    console.print("[dim]Ouvindo...[/dim]")
                    rec.adjust_for_ambient_noise(source)
                    audio = rec.listen(source, timeout=5, phrase_time_limit=5)
                comando = rec.recognize_google(audio, language='pt-BR').lower()
                console.print(f"[yellow]Você disse:[/yellow] {comando}")

            if 'modo chat' in comando: usar_voz = False; falar("Ativando teclado."); continue
            elif 'modo voz' in comando: usar_voz = True; falar("Ativando microfone."); continue

            elif 'gatilhos' in comando or 'suas funções' in comando:
                lista = "[cyan]buscar anime:[/cyan] Jikan\n[cyan]ler pdf:[/cyan] Grande Sábio\n[cyan]sentido aranha:[/cyan] Hardware\n[cyan]processos abertos:[/cyan] Radar\n[cyan]analise a tela:[/cyan] Visão\n[cyan]escanear:[/cyan] Radar\n[cyan]abrir/fechar [app]:[/cyan] Controle de App\n[cyan]print:[/cyan] Captura"
                console.print(Panel(lista, title="[bold magenta]🛠️ MANUAL DA ASTRA 🛠️[/bold magenta]"))
                falar("Exibindo o manual com nossos bebês."); continue

            elif any(g in comando for g in gatilhos_hardware): falar(relatorio_hardware()); continue

            elif any(g in comando for g in gatilhos_processos):
                falar(radar_de_processos())
                continue
            
            elif any(g in comando for g in gatilhos_anime):
                for g in gatilhos_anime: comando = comando.replace(g, '')
                comando = comando.replace('astra', '').strip()
                if comando: falar(rastreador_otaku(comando))
                continue

            elif any(g in comando for g in gatilhos_pdf):
                for g in gatilhos_pdf: comando = comando.replace(g, '')
                comando = comando.replace('.pdf', '').replace('astra', '').strip()
                if comando: falar(estudar_pdf(comando))
                continue
            
            elif any(g in comando for g in gatilhos_visao):
                for g in gatilhos_visao: comando = comando.replace(g, '')
                falar(analisar_tela(comando.strip())); continue

            elif 'escanear' in comando: falar(escanear_sistema()); continue

            elif 'volume' in comando:
                numeros = re.findall(r'\d+', comando)
                if numeros: falar(mudar_volume(int(numeros[0]))); continue

            elif 'brilho' in comando:
                numeros = [int(s) for s in comando.split() if s.isdigit()]
                if numeros: falar(mudar_brilho(numeros[0])); continue

            elif 'print' in comando: falar(tirar_print()); continue
            elif 'esvaziar lixeira' in comando: winshell.recycle_bin().empty(confirm=False, sound=True); falar("Lixeira esvaziada."); continue
            elif 'desligar' in comando and 'pc' in comando: falar("Encerrando."); os.system("shutdown /s /t 10"); break
            
            elif 'tocar' in comando:
                musica = comando.replace('tocar', '').strip()
                falar(f"Tocando {musica}."); pywhatkit.playonyt(musica); continue
            
            elif 'clima' in comando:
                cidade = comando.replace('clima', '').replace('em', '').strip()
                falar(obter_clima(cidade)); continue

            elif any(g in comando for g in gatilhos_busca):
                for g in gatilhos_busca: comando = comando.replace(g, '')
                falar(pesquisa_inteligente(comando.replace('astra', '').strip())); continue
            

            elif 'sair' in comando: break

            elif 'abrir' in comando:
                nome_app = comando.replace('abrir', '').strip()
                falar(f"Iniciando {nome_app}...")
                abriu = False
                try:
                    with open(ARQUIVO_APPS, "r", encoding="utf-8") as f:
                        for nome, caminho in json.load(f).items():
                            if nome_app in nome: os.startfile(caminho); abriu = True; break
                except: pass
                if not abriu:
                    try: app_open(nome_app, match_closest=True, output=False) 
                    except: falar("App não encontrado.")
                continue

            elif 'fechar' in comando:
                nome_app = comando.replace('fechar', '').strip()
                falar(f"Ativando protocolo de aniquilação para {nome_app}...")
                try: 
                    app_close(nome_app, match_closest=True, output=False)
                    falar(f"BUM! {nome_app} foi explodido e removido da RAM.")
                except: 
                    falar("As minhas lentes não acharam esse bebê rodando. Ele já deve estar morto.")
                continue

            else:
                resposta, context_chat = cerebro_astra(comando, context_chat)
                falar(resposta)

        except sr.WaitTimeoutError: pass 
        except sr.UnknownValueError: pass 
        except sr.RequestError: falar("Minha audição falhou.")
        except KeyboardInterrupt: break

if __name__ == "__main__":
    main()