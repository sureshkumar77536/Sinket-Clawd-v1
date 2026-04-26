#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
import urllib.request
from urllib.error import HTTPError

# ─── Auto-install dependencies ───
def ensure_deps():
    try:
        import textual
        import rich
    except ImportError:
        print("\033[1;36m📦 Installing dependencies...\033[0m")
        os.system("pip3 install textual rich --break-system-packages 2>/dev/null || pip3 install textual rich --user 2>/dev/null || pip3 install textual rich")
        print("\033[1;32m✅ Done! Run 'sinkwd' again.\033[0m")
        sys.exit(0)

ensure_deps()

from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Container, Horizontal
from textual.widgets import Input, Static, Label, Button
from textual.binding import Binding
from textual.reactive import reactive
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.console import Console

CONFIG_PATH = os.path.expanduser("~/.sinket_config.json")
HISTORY_PATH = os.path.expanduser("~/.sinket_history.json")
REPO_DIR = os.path.expanduser("~/.sinket_clawd")

# ─── ZEN THEME CSS ───
ZEN_CSS = """
Screen { align: center middle; background: #0d1117; }

.main-container { width: 100%; height: 100%; background: #0d1117; }

/* Header Bar */
.header-bar { 
    height: 3; 
    background: #161b22; 
    color: #39c5cf; 
    content-align: center middle;
    text-style: bold;
    border: solid #30363d;
    border-title-color: #39c5cf;
}

/* Status Bar */
.status-bar { 
    height: 1; 
    background: #0d1117; 
    color: #8b949e; 
    padding: 0 2;
    text-style: dim;
}

/* Chat Area */
.chat-scroll { 
    width: 100%; 
    height: 1fr; 
    background: #0d1117; 
    padding: 0 1;
}

/* User Message Bubble */
.message-user { 
    width: 100%; 
    height: auto; 
    margin: 1 0;
    background: #161b22;
    color: #39c5cf;
    padding: 1 2;
    border-left: outer #39c5cf;
}

/* AI Message Bubble */
.message-ai { 
    width: 100%; 
    height: auto; 
    margin: 1 0;
    background: #161b22;
    color: #c9d1d9;
    padding: 1 2;
    border-left: outer #238636;
}

/* Thinking Indicator */
.thinking-box { 
    width: 100%; 
    height: auto; 
    margin: 1 0;
    background: #161b22;
    color: #39c5cf;
    padding: 1 2;
    border-left: outer #39c5cf;
    text-style: italic blink;
}

/* Input Area */
.input-row { 
    height: auto; 
    background: #161b22; 
    padding: 0 1;
    border-top: solid #30363d;
}

Input { 
    background: #0d1117; 
    color: #39c5cf; 
    border: none; 
    padding: 1 2;
}

Input:focus { 
    border: none; 
}

/* Setup Modal */
.setup-modal { 
    background: #161b22; 
    color: #c9d1d9; 
    border: thick #39c5cf; 
    padding: 2 4; 
    width: 70; 
    height: auto;
}

.setup-modal Label { 
    color: #39c5cf; 
    text-style: bold; 
    margin: 1 0 0 0;
}

.setup-modal Input { 
    background: #0d1117; 
    border: tall #30363d; 
    margin: 0 0 1 0;
    color: #c9d1d9;
}

Button { 
    background: #238636; 
    color: white; 
    margin: 1 2 0 0;
}

Button:hover { 
    background: #2ea043; 
}

Button#cancel { 
    background: #da3633; 
}

Button#cancel:hover { 
    background: #f85149; 
}
"""

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
        json.dump(history[-100:], f)

# ─── UI WIDGETS ───

class ZenHeader(Static):
    def render(self):
        return Panel.fit(
            "[bold cyan]⚡ SINKET CLAWD v2[/bold cyan] [dim]—[/dim] [bold green]Zen Edition[/bold green]",
            style="cyan",
            border_style="cyan",
            padding=(0, 2)
        )

class MessageUser(Static):
    def __init__(self, text: str):
        self.msg_text = text
        super().__init__()

    def render(self):
        # User message with cyan styling
        content = Text(self.msg_text, style="bold cyan")
        return Panel(
            content,
            title="[bold white]╭─ You ─╮[/bold white]",
            title_align="right",
            border_style="cyan",
            style="on #161b22",
            padding=(1, 2)
        )

class MessageAI(Static):
    def __init__(self, text: str = ""):
        self.msg_text = text
        super().__init__()

    def render(self):
        if not self.msg_text:
            return Panel("", border_style="green")
        # AI message with markdown + code highlighting
        md = Markdown(self.msg_text, code_theme="monokai")
        return Panel(
            md,
            title="[bold green]╭─ Sinket ─╮[/bold green]",
            title_align="left",
            border_style="green",
            style="on #161b22",
            padding=(1, 2)
        )

class ThinkingIndicator(Static):
    thinking_dots = reactive("●")

    def render(self):
        return Panel(
            f"[bold cyan]{self.thinking_dots}[/bold cyan] [dim]thinking...[/dim]",
            title="[dim]╭─ ... ─╮[/dim]",
            title_align="left",
            border_style="cyan",
            style="on #161b22",
            padding=(1, 2)
        )

    def on_mount(self):
        self.animate_dots()

    def animate_dots(self):
        dots = ["●", "● ●", "● ● ●", "● ●", "●"]
        idx = 0
        def cycle():
            nonlocal idx
            self.thinking_dots = dots[idx % len(dots)]
            idx += 1
            self.set_timer(0.5, cycle)
        cycle()

class SetupModal(Container):
    def compose(self) -> ComposeResult:
        yield ZenHeader()
        yield Label("🔧 [bold cyan]API Provider Setup[/bold cyan]", id="setup-title")
        yield Label("Base URL:", id="lbl-url")
        yield Input(placeholder="https://api.openai.com/v1", id="base_url", value=load_config().get("base_url", ""))
        yield Label("Model Name:", id="lbl-model")
        yield Input(placeholder="gpt-4", id="model", value=load_config().get("model", ""))
        yield Label("API Key (optional):", id="lbl-key")
        yield Input(placeholder="sk-...", id="token", password=True, value=load_config().get("token", ""))
        with Horizontal():
            yield Button("💾 Save & Connect", id="save", variant="success")
            yield Button("❌ Cancel", id="cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            base = self.query_one("#base_url", Input).value.strip()
            model = self.query_one("#model", Input).value.strip()
            token = self.query_one("#token", Input).value.strip()
            
            if not base:
                self.query_one("#lbl-url").update("[bold red]Base URL: * REQUIRED[/bold red]")
                return
            if not model:
                self.query_one("#lbl-model").update("[bold red]Model Name: * REQUIRED[/bold red]")
                return
                
            config = {"base_url": base, "model": model, "token": token}
            save_config(config)
            self.app.config = config
            self.app.update_status()
            self.app.pop_screen()
            self.app.query_one("#chat-input", Input).focus()
            self.app.notify("✅ Connected!", severity="information", timeout=2)
        else:
            self.app.pop_screen()
            self.app.query_one("#chat-input", Input).focus()

# ─── MAIN APP ───

class SinketApp(App):
    CSS = ZEN_CSS
    BINDINGS = [
        Binding("ctrl+s", "setup", "⚙️ Settings"),
        Binding("ctrl+l", "clear", "🧹 Clear"),
        Binding("ctrl+q", "quit", "❌ Exit"),
    ]

    config = reactive(load_config())
    history = reactive(load_history())
    is_thinking = reactive(False)

    def compose(self) -> ComposeResult:
        # Top Status Bar
        model_name = self.config.get("model", "Not Set")
        status = "[green]●[/green]" if self.config.get("base_url") else "[red]●[/red]"
        yield Static(f"  [bold cyan]SINKET CLAWD v2[/bold cyan] [dim]|[/dim] Model: [cyan]{model_name}[/cyan] {status} [dim]| Ctrl+S Settings | Ctrl+L Clear | Ctrl+Q Exit[/dim]", classes="status-bar")
        
        # Chat Messages Area
        with VerticalScroll(id="chat-scroll", classes="chat-scroll"):
            for msg in self.history[-30:]:
                if msg["role"] == "user":
                    yield MessageUser(msg["content"])
                else:
                    yield MessageAI(msg["content"])
        
        # Thinking Indicator (hidden by default)
        yield ThinkingIndicator(id="thinking")
        
        # Input Area
        with Container(classes="input-row"):
            yield Input(placeholder="❯  Type message or /command …", id="chat-input")

    def on_mount(self):
        self.query_one("#thinking", ThinkingIndicator).display = False
        self.query_one("#chat-input", Input).focus()
        if not self.config.get("base_url"):
            self.push_screen(SetupModal())

    def update_status(self):
        model_name = self.config.get("model", "Not Set")
        status = "[green]●[/green]" if self.config.get("base_url") else "[red]●[/red]"
        self.query_one(".status-bar", Static).update(
            f"  [bold cyan]SINKET CLAWD v2[/bold cyan] [dim]|[/dim] Model: [cyan]{model_name}[/cyan] {status} [dim]| Ctrl+S Settings | Ctrl+L Clear | Ctrl+Q Exit[/dim]"
        )

    def action_setup(self):
        self.push_screen(SetupModal())

    def action_clear(self):
        self.history = []
        save_history(self.history)
        chat_scroll = self.query_one("#chat-scroll", VerticalScroll)
        chat_scroll.remove_children()
        self.notify("🧹 History cleared!", severity="information", timeout=2)

    def scroll_to_bottom(self):
        scroll = self.query_one("#chat-scroll", VerticalScroll)
        scroll.scroll_end(animate=True)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_text = event.value.strip()
        if not user_text:
            return
        self.query_one("#chat-input", Input).value = ""

        cmd = user_text.lower()

        if cmd == "/exit":
            self.exit()
            return
        elif cmd == "/clear":
            self.action_clear()
            return
        elif cmd == "/provider":
            self.push_screen(SetupModal())
            return
        elif cmd == "/update":
            await self.do_update()
            return

        # Add user message to UI
        self.history.append({"role": "user", "content": user_text})
        save_history(self.history)
        
        chat_scroll = self.query_one("#chat-scroll", VerticalScroll)
        await chat_scroll.mount(MessageUser(user_text))
        self.scroll_to_bottom()

        # Show thinking animation
        self.is_thinking = True
        thinking = self.query_one("#thinking", ThinkingIndicator)
        thinking.display = True
        self.scroll_to_bottom()

        # Call API
        reply = await self.call_api()

        # Hide thinking
        thinking.display = False
        self.is_thinking = False

        if reply:
            # Typewriter effect with smooth reveal
            ai_msg = MessageAI("")
            await chat_scroll.mount(ai_msg)
            self.scroll_to_bottom()

            words = reply.split(" ")
            displayed = ""
            for i, word in enumerate(words):
                displayed += word + (" " if i < len(words) - 1 else "")
                ai_msg.msg_text = displayed
                ai_msg.refresh()
                self.scroll_to_bottom()
                await self.sleep(0.012)  # Smooth 12ms per word

            self.history.append({"role": "assistant", "content": reply})
            save_history(self.history)

    async def call_api(self):
        if not self.config.get("base_url"):
            return "❌ No API configured. Press [bold]Ctrl+S[/bold] to setup."

        endpoint = self.config["base_url"]
        if not endpoint.endswith("/chat/completions"):
            endpoint = endpoint.rstrip("/") + "/chat/completions"

        req_data = json.dumps({
            "model": self.config["model"],
            "messages": self.history
        }).encode('utf-8')

        headers = {"Content-Type": "application/json"}
        if self.config.get("token"):
            headers["Authorization"] = f"Bearer {self.config['token']}"

        req = urllib.request.Request(endpoint, data=req_data, headers=headers, method="POST")

        try:
            import asyncio
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=120))
            resp_data = json.loads(resp.read().decode('utf-8'))
            return resp_data["choices"][0]["message"]["content"]
        except HTTPError as e:
            err = e.read().decode('utf-8')[:300]
            return f"❌ [bold red]API Error {e.code}[/bold red]: {err}"
        except Exception as e:
            return f"❌ [bold red]Error:[/bold red] {str(e)}"

    async def do_update(self):
        chat_scroll = self.query_one("#chat-scroll", VerticalScroll)
        await chat_scroll.mount(MessageAI("🔄 [bold cyan]Updating via GitHub...[/bold cyan]"))
        self.scroll_to_bottom()

        if not os.path.exists(REPO_DIR):
            await chat_scroll.mount(MessageAI("❌ Repository not found."))
            return

        try:
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: subprocess.run(
                ["git", "-C", REPO_DIR, "fetch", "--all"], 
                check=True, capture_output=True
            ))
            await loop.run_in_executor(None, lambda: subprocess.run(
                ["git", "-C", REPO_DIR, "reset", "--hard", "origin/main"], 
                check=True, capture_output=True
            ))
            await chat_scroll.mount(MessageAI("✅ [bold green]Update complete! Restarting...[/bold green]"))
            await self.sleep(1.5)
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            await chat_scroll.mount(MessageAI(f"❌ [bold red]Update failed:[/bold red] {str(e)}"))

    async def sleep(self, seconds: float):
        import asyncio
        await asyncio.sleep(seconds)

if __name__ == "__main__":
    app = SinketApp()
    app.run()
