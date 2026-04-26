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
    from rich.text import Text
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
                                              
 ██████╗██╗      █████╗ ██╗    ██╗██████╗ 
██╔════╝██║     ██╔══██╗██║    ██║██╔══██╗
██║     ██║     ███████║██║ █╗ ██║██║  ██║
██║     ██║     ██╔══██║██║███╗██║██║  ██║
╚██████╗███████╗██║  ██║╚███╔███╔╝██████╔╝
 ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚═════╝ 
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
    console.print(Panel("[bold cyan]WELCOME TO SINKET CLAWD SETUP[/bold cyan]\n[dim]Configure ANY OpenAI-compatible API Provider.[/dim]", border_style="cyan"))

    if is_reconfigure:
        console.print("[dim italic]Type 'exit' in Base URL to cancel and return to chat.[/dim italic]\n")

    base_url = Prompt.ask("[bold cyan]Enter API Base URL[/bold cyan] [dim](e.g., https://api.openai.com/v1)[/dim]")
    if is_reconfigure and base_url.strip().lower() == 'exit':
        return load_config()

    model = Prompt.ask("[bold cyan]Enter Model Name[/bold cyan] [dim](e.g., gpt-4, claude-3)[/dim]")
    token = Prompt.ask("[bold cyan]Enter API Token/Key[/bold cyan] [dim](Leave blank if none required)[/dim]", password=True)

    config = {"base_url": base_url.strip(), "model": model.strip(), "token": token.strip()}
    save_config(config)
    console.print("\n[bold green]✅ Setup Saved Successfully! Booting Sinket Clawd...[/bold green]")
    time.sleep(1.5)
    return config

def update_app():
    console.print("\n[bold cyan]🔄 Updating Sinket Clawd via GitHub...[/bold cyan]")
    if os.path.exists(REPO_DIR):
        try:
            subprocess.run(["git", "-C", REPO_DIR, "pull", "origin", "main"], check=True)
            console.print("[bold green]✅ Update complete! Restarting...[/bold green]")
            time.sleep(1)
            os.execv(sys.executable, ['python3'] + sys.argv)
        except subprocess.CalledProcessError:
            console.print("[bold red]❌ Failed to update. Please check git repository.[/bold red]")
            time.sleep(2)
    else:
        console.print("[bold red]❌ Repository directory not found. Cannot auto-update.[/bold red]")
        time.sleep(2)

def chat_loop():
    config = load_config()
    if not config.get("base_url"):
        config = setup_provider()

    history = load_history()

    while True:
        console.clear()
        console.print(ASCII_ART, justify="center")
        header_text = f"[bold cyan]Model:[/bold cyan] {config.get('model')} | [bold cyan]Commands:[/bold cyan] /provider, /update, /clear, /exit"
        console.print(Panel(header_text, border_style="cyan"))
        
        # Display chat history in UI
        for msg in history[-6:]:
            if msg["role"] == "user":
                console.print(f"[bold cyan]YOU:[/bold cyan] {msg['content']}\n")
            else:
                console.print(f"[bold white]SINKET:[/bold white] {msg['content']}\n")

        try:
            user_input = Prompt.ask("[bold cyan]❯[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input.strip():
            continue

        cmd = user_input.strip().lower()
        if cmd == "/exit":
            console.print("[bold cyan]👋 Bye! Session ended.[/bold cyan]")
            break
        elif cmd == "/clear":
            history = []
            save_history(history)
            continue
        elif cmd == "/provider":
            new_config = setup_provider(is_reconfigure=True)
            if new_config:
                config = new_config
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

        console.print("[bold cyan]SINKET is thinking...[/bold cyan]")
        
        try:
            resp = urllib.request.urlopen(req, timeout=120)
            resp_data = json.loads(resp.read().decode('utf-8'))
            reply = resp_data["choices"][0]["message"]["content"]
            history.append({"role": "assistant", "content": reply})
            save_history(history)
        except HTTPError as e:
            err_body = e.read().decode('utf-8')
            console.print(f"[bold red]❌ API Error {e.code}:[/bold red] {err_body}")
            history.pop()
            time.sleep(4)
        except Exception as e:
            console.print(f"[bold red]❌ Error:[/bold red] {str(e)}")
            history.pop()
            time.sleep(4)

if __name__ == "__main__":
    chat_loop()
