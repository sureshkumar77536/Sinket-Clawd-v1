#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
import urllib.request
from urllib.error import HTTPError

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.markdown import Markdown
    from rich.live import Live
except ImportError:
    os.system("pip3 install rich --break-system-packages || pip3 install rich")
    print("Dependencies installed. Please run 'sinkwd' again.")
    sys.exit(0)

console = Console()
CONFIG_PATH = os.path.expanduser("~/.sinket_config.json")
HISTORY_PATH = os.path.expanduser("~/.sinket_history.json")
REPO_DIR = os.path.expanduser("~/.sinket_clawd")

ASCII_ART = """[bold cyan]
███████╗██╗███╗   ██╗██╗  ██╗███████╗████████╗
██╔════╝██║████╗  ██║██║ ██╔╝██╔════╝╚══██╔══╝
███████╗██║██╔██╗ ██║█████╔╝ █████╗     ██║   
╚════██║██║██║╚██╗██║██╔═██╗ ██╔══╝     ██║   
███████║██║██║ ╚████║██║  ██╗███████╗   ██║   
╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝   ╚═╝   
[/bold cyan]"""

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)

def load_history():
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "r") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f)

def setup_provider(is_reconfigure=False):
    console.clear()
    console.print(ASCII_ART, justify="center")
    console.print(Panel("[bold cyan]SETUP[/bold cyan]\n[dim]Configure API Provider.[/dim]", border_style="cyan"))

    if is_reconfigure:
        console.print("[dim italic]Type 'exit' in Base URL to cancel.[/dim italic]\n")

    base_url = Prompt.ask("[bold cyan]Base URL[/bold cyan]")
    if is_reconfigure and base_url.strip().lower() == 'exit':
        return load_config()

    model = Prompt.ask("[bold cyan]Model Name[/bold cyan]")
    token = Prompt.ask("[bold cyan]Token/Key[/bold cyan]", password=True)

    config = {"base_url": base_url.strip(), "model": model.strip(), "token": token.strip()}
    save_config(config)
    console.print("\n[bold green]✅ Saved![/bold green]")
    time.sleep(1)
    return config

def update_app():
    console.print("\n[bold cyan]🔄 Updating via GitHub...[/bold cyan]")
    if os.path.exists(REPO_DIR):
        try:
            # Pura forcefully update karega, error nahi aayega ab
            subprocess.run(["git", "-C", REPO_DIR, "fetch", "--all"], check=True)
            subprocess.run(["git", "-C", REPO_DIR, "reset", "--hard", "origin/main"], check=True)
            console.print("[bold green]✅ Update complete! Restarting...[/bold green]")
            time.sleep(1)
            os.execv(sys.executable, ['python3'] + sys.argv)
        except subprocess.CalledProcessError:
            console.print("[bold red]❌ Update failed. Please check repository.[/bold red]")
            time.sleep(2)
    else:
        console.print("[bold red]❌ Repository not found. Cannot auto-update.[/bold red]")
        time.sleep(2)

def print_header(config):
    console.clear()
    # Ekdum clean open code zen jaisa header
    header_text = f"[bold white]# SINKET CLAWD Workspace[/bold white]   [dim]Model: {config.get('model')} | Commands: /provider, /update, /clear, /exit[/dim]"
    console.print(Panel(header_text, border_style="dim cyan", padding=(0, 1)))
    console.print("")

def chat_loop():
    config = load_config()
    if not config.get("base_url"):
        config = setup_provider()

    history = load_history()
    print_header(config)

    if history:
        console.print("[dim]Loading history...[/dim]\n")
        for msg in history[-4:]:
            if msg["role"] == "user":
                console.print(f"[bold white]User[/bold white]")
                console.print(f"[cyan]>[/cyan] {msg['content']}\n")
            else:
                console.print(f"[bold cyan]Sinket[/bold cyan]")
                console.print(Markdown(msg['content']))
                console.print("")

    while True:
        # Minimalistic input block theme
        console.print("[dim]┌─ Input[/dim]")
        sys.stdout.write("\033[2m│\033[0m \033[1;36m❯\033[0m ")
        sys.stdout.flush()
        try:
            user_input = input().strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            break
        console.print("[dim]└──────────────[/dim]")

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd == "/exit":
            break
        elif cmd == "/clear":
            history = []
            save_history(history)
            print_header(config)
            continue
        elif cmd == "/provider":
            new_config = setup_provider(is_reconfigure=True)
            if new_config:
                config = new_config
            print_header(config)
            continue
        elif cmd == "/update":
            update_app()
            continue

        history.append({"role": "user", "content": user_input})
        save_history(history)

        endpoint = config["base_url"]
        if not endpoint.endswith("/chat/completions"):
            endpoint = endpoint.rstrip("/") + "/chat/completions"

        req_data = json.dumps({
            "model": config["model"],
            "messages": history
        }).encode('utf-8')

        headers = {"Content-Type": "application/json"}
        if config.get("token"):
            headers["Authorization"] = f"Bearer {config['token']}"

        req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")

        reply = ""
        console.print("")
        with console.status("[cyan]Thinking...[/cyan]", spinner="dots", spinner_style="cyan"):
            try:
                resp = urllib.request.urlopen(req, timeout=120)
                resp_data = json.loads(resp.read().decode('utf-8'))
                reply = resp_data["choices"][0]["message"]["content"]
            except HTTPError as e:
                err_body = e.read().decode('utf-8')
                reply = f"❌ API Error {e.code}: {err_body}"
                console.print(f"[bold red]{reply}[/bold red]")
                history.pop()
                continue
            except Exception as e:
                reply = f"❌ Error: {str(e)}"
                console.print(f"[bold red]{reply}[/bold red]")
                history.pop()
                continue

        console.print("[bold cyan]Sinket[/bold cyan]")
        words = reply.split(" ")
        displayed = ""
        
        with Live(console=console, auto_refresh=False, vertical_overflow="visible") as live:
            for i, word in enumerate(words):
                displayed += word + (" " if i < len(words) - 1 else "")
                live.update(Markdown(displayed), refresh=True)
                time.sleep(0.015) 
        
        console.print("\n") 
        history.append({"role": "assistant", "content": reply})
        save_history(history)

if __name__ == "__main__":
    chat_loop()
