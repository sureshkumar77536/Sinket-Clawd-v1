#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
import urllib.request
from urllib.error import HTTPError

# ─── Auto-install dependencies if missing ───
def ensure_deps():
    try:
        import textual
        import rich
    except ImportError:
        print("📦 Installing dependencies...")
        os.system("pip3 install textual rich --break-system-packages 2>/dev/null || pip3 install textual rich --user 2>/dev/null || pip3 install textual rich")
        print("✅ Done! Please run 'sinkwd' again.")
        sys.exit(0)

ensure_deps()

from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Container, Horizontal
from textual.widgets import Input, Static, Header, Footer, Label, Button
from textual.binding import Binding
from textual.reactive import reactive
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text

CONFIG_PATH = os.path.expanduser("~/.sinket_config.json")
HISTORY_PATH = os.path.expanduser("~/.sinket_history.json")
REPO_DIR = os.path.expanduser("~/.sinket_clawd")

ZEN_CSS = """
Screen { align: center middle; }
.main-container { width: 100%; height: 100%; background: #0d1117; }
.chat-scroll { width: 100%; height: 1fr; background: #0d1117; padding: 0 1; }
.message-user { width: 100%; height: auto; margin: 1 0; }
.message-ai { width: 100%; height: auto; margin: 1 0; }
.user-bubble { background: #161b22; color: #39c5cf; padding: 1 2; border-left: thick #39c5cf; }
.ai-bubble { background: #161b22; color: #c9d1d9; padding: 1 2; border-left: thick #238636; }
.thinking-bubble { background: #161b22; color: #39c5cf; padding: 1 2; border-left: thick #39c5cf; text-style: italic; }
.input-row { height: auto; background: #161b22; padding: 0 1; }
Input { background: #0d1117; color: #39c5cf; border: none; padding: 1 2; }
Input:focus { border: none; }
.status-bar { height: 1; background: #161b22; color: #8b949e; padding: 0 2; }
.setup-modal { background: #161b22; color: #c9d1d9; border: thick #39c5cf; padding: 2 4; width: 60; height: auto; }
.setup-modal Input { background: #0d1117; border: tall #30363d; margin: 1 0; }
.setup-modal Button { background: #238636; color: white; margin: 1 0; }
.setup-modal Button:hover { background: #2ea043; }
.title-bar { height: 1; background: #161b22; color: #39c5cf; content-align: center middle; text-style: bold; }
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
        json.dump(history[-100:], f)  # Keep last 100 only

class SetupModal(Container):
    def compose(self) -> ComposeResult:
        yield Label("⚙️  API Provider Setup", classes="title-bar")
        yield Label("Base URL:", id="lbl-url")
        yield Input(placeholder="https://api.openai.com/v1", id="base_url")
        yield Label("Model Name:", id="lbl-model")
        yield Input(placeholder="gpt-4", id="model")
        yield Label("API Key:", id="lbl-key")
        yield Input(placeholder="sk-...", id="token", password=True)
        with Horizontal():
            yield Button("💾 Save", id="save", variant="success")
            yield Button("❌ Cancel", id="cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            base = self.query_one("#base_url", Input).value.strip()
            model = self.query_one("#model", Input).value.strip()
            token = self.query_one("#token", Input).value.strip()
            if not base or not model:
                self.query_one("#lbl-url").update("[red]Base URL: *required[/red]")
                return
            config = {"base_url": base, "model": model, "token": token}
            save_config(config)
            self.app.config = config
            self.app.pop_screen()
            self.app.query_one("#chat-input", Input).focus()
        else:
            self.app.pop_screen()
            self.app.query_one("#chat-input", Input).focus()

class MessageUser(Static):
    def __init__(self, text: str):
        self.text = text
        super().__init__()

    def render(self):
        return Panel(self.text, style="bold cyan", border_style="cyan", title="[bold white]You[/bold white]", title_align="right")

class MessageAI(Static):
    def __init__(self, text: str):
        self.text = text
        super().__init__()

    def render(self):
        md = Markdown(self.text, code_theme="monokai")
        return Panel(md, style="white", border_style="green", title="[bold cyan]Sinket[/bold cyan]", title_align="left")

class ThinkingIndicator(Static):
    def render(self):
        return Panel("● ● ●  thinking...", style="italic cyan", border_style="cyan")

class SinketApp(App):
    CSS = ZEN_CSS
    BINDINGS = [
        Binding("ctrl+s", "setup", "Settings"),
        Binding("ctrl+c", "quit", "Quit"),
    ]

    config = reactive(load_config())
    history = reactive(load_history())
    is_thinking = reactive(False)

    def compose(self) -> ComposeResult:
        yield Static("⚡ SINKET CLAWD v2  —  Zen Edition", classes="title-bar")
        yield Static(f"Model: {self.config.get('model','Not Set')}  |  Ctrl+S: Settings  |  /exit /clear /update /provider", classes="status-bar")
        with VerticalScroll(id="chat-scroll", classes="chat-scroll"):
            for msg in self.history[-20:]:
                if msg["role"] == "user":
                    yield MessageUser(msg["content"])
                else:
                    yield MessageAI(msg["content"])
        yield ThinkingIndicator(id="thinking", classes="thinking-bubble")
        yield Input(placeholder="❯  Type a message or /command …", id="chat-input")

    def on_mount(self):
        self.query_one("#thinking", ThinkingIndicator).display = False
        self.query_one("#chat-input", Input).focus()
        if not self.config.get("base_url"):
            self.push_screen(SetupModal())

    def action_setup(self):
        self.push_screen(SetupModal())

    def scroll_to_bottom(self):
        scroll = self.query_one("#chat-scroll", VerticalScroll)
        scroll.scroll_end(animate=False)

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
            self.history = []
            save_history(self.history)
            chat_scroll = self.query_one("#chat-scroll", VerticalScroll)
            chat_scroll.remove_children()
            return
        elif cmd == "/provider":
            self.push_screen(SetupModal())
            return
        elif cmd == "/update":
            await self.do_update()
            return

        # Add user message
        self.history.append({"role": "user", "content": user_text})
        save_history(self.history)
        chat_scroll = self.query_one("#chat-scroll", VerticalScroll)
        await chat_scroll.mount(MessageUser(user_text))
        self.scroll_to_bottom()

        # Show thinking
        self.is_thinking = True
        thinking = self.query_one("#thinking", ThinkingIndicator)
        thinking.display = True
        self.scroll_to_bottom()

        # Call API in background
        reply = await self.call_api()

        # Hide thinking
        thinking.display = False
        self.is_thinking = False

        if reply:
            # Typewriter effect
            ai_msg = MessageAI("")
            await chat_scroll.mount(ai_msg)
            self.scroll_to_bottom()

            words = reply.split(" ")
            displayed = ""
            for i, word in enumerate(words):
                displayed += word + (" " if i < len(words) - 1 else "")
                ai_msg.text = displayed
                ai_msg.refresh()
                self.scroll_to_bottom()
                await self.sleep(0.015)

            self.history.append({"role": "assistant", "content": reply})
            save_history(self.history)

    async def call_api(self):
        if not self.config.get("base_url"):
            return "❌ No API configured. Press Ctrl+S to setup."

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
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=120))
            resp_data = json.loads(resp.read().decode('utf-8'))
            return resp_data["choices"][0]["message"]["content"]
        except HTTPError as e:
            return f"❌ API Error {e.code}: {e.read().decode('utf-8')[:200]}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    async def do_update(self):
        chat_scroll = self.query_one("#chat-scroll", VerticalScroll)
        await chat_scroll.mount(MessageAI("🔄 Updating via GitHub..."))
        self.scroll_to_bottom()

        if not os.path.exists(REPO_DIR):
            await chat_scroll.mount(MessageAI("❌ Repository not found."))
            return

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: subprocess.run(["git", "-C", REPO_DIR, "fetch", "--all"], check=True, capture_output=True))
            await loop.run_in_executor(None, lambda: subprocess.run(["git", "-C", REPO_DIR, "reset", "--hard", "origin/main"], check=True, capture_output=True))
            await chat_scroll.mount(MessageAI("✅ Update complete! Restarting..."))
            await self.sleep(1)
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            await chat_scroll.mount(MessageAI(f"❌ Update failed: {str(e)}"))

    async def sleep(self, seconds: float):
        import asyncio
        await asyncio.sleep(seconds)

if __name__ == "__main__":
    import asyncio
    app = SinketApp()
    app.run()
