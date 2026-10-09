import hashlib
import queue
import re
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .network import NetworkClient
from .theme import (
    ACCENT,
    ACCENT_ACTIVE,
    APP_BG,
    BORDER,
    DANGER,
    ENTRY_BG,
    FONT_FAMILY,
    MUTED,
    NAME_COLORS,
    SUCCESS,
    SURFACE,
    SYSTEM,
    TEXT,
)


class NameDialog:
    """Diálogo modal pequeño para solicitar el nombre antes de entrar."""

    def __init__(self, parent):
        self.parent = parent
        self.result = None

        self.window = tk.Toplevel(parent)
        self.window.title("Entrar a la sala")
        self.window.configure(bg=SURFACE)
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self._cancel)

        frame = tk.Frame(self.window, bg=SURFACE, padx=28, pady=24)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="Elige tu nombre",
            bg=SURFACE,
            fg=TEXT,
            font=(FONT_FAMILY, 15, "bold"),
        ).pack(anchor="w")

        tk.Label(
            frame,
            text="El servidor resolverá automáticamente nombres repetidos.",
            bg=SURFACE,
            fg=MUTED,
            font=(FONT_FAMILY, 9),
        ).pack(anchor="w", pady=(4, 14))

        self.name_var = tk.StringVar()
        self.entry = ttk.Entry(
            frame,
            textvariable=self.name_var,
            width=34,
            style="Chat.TEntry",
        )
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", self._accept)

        self.error_label = tk.Label(
            frame,
            text="",
            bg=SURFACE,
            fg=DANGER,
            font=(FONT_FAMILY, 9),
        )
        self.error_label.pack(anchor="w", pady=(6, 0))

        actions = tk.Frame(frame, bg=SURFACE)
        actions.pack(fill="x", pady=(16, 0))

        ttk.Button(
            actions,
            text="Cancelar",
            command=self._cancel,
            style="Secondary.TButton",
        ).pack(side="right")

        ttk.Button(
            actions,
            text="Entrar",
            command=self._accept,
            style="Accent.TButton",
        ).pack(side="right", padx=(0, 8))

        self.window.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.window.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.window.winfo_height()) // 2
        self.window.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.entry.focus_set()

    def show(self):
        self.parent.wait_window(self.window)
        return self.result

    def _accept(self, _event=None):
        name = self.name_var.get().strip()

        if not name:
            self.error_label.config(text="El nombre no puede estar vacío.")
            return

        if len(name) > 24:
            self.error_label.config(text="Usa como máximo 24 caracteres.")
            return

        self.result = name
        self.window.destroy()

    def _cancel(self):
        self.result = None
        self.window.destroy()


class ChatApp:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.root = tk.Tk()
        self.root.title("Sala de chat")
        self.root.geometry("980x620")
        self.root.minsize(780, 500)
        self.root.configure(bg=APP_BG)

        # Tkinter debe modificarse únicamente desde su hilo principal.
        # El hilo de red deposita aquí los eventos recibidos.
        self.incoming_queue = queue.Queue()
        self.network = NetworkClient(
            host=self.host,
            port=self.port,
            incoming_queue=self.incoming_queue,
        )

        self.username = None
        self.connected = False
        self.join_accepted = False

        # Caché local de eventos ya recibidos. El servidor sigue siendo la
        # autoridad: los mensajes entran aquí únicamente después de volver por TCP.
        self.message_cache = {}
        self.messages_without_id = []
        self.participants = []

        self._configure_styles()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def run(self):
        self._set_connection_state("connecting", f"Conectando con {self.host}:{self.port}...")

        try:
            self.network.connect()
        except OSError as exc:
            messagebox.showerror(
                "No se pudo conectar",
                f"No fue posible conectarse con {self.host}:{self.port}\n\n{exc}",
                parent=self.root,
            )
            self.root.destroy()
            return

        self.connected = True
        self._set_connection_state("connected", f"Servidor {self.host}:{self.port}")

        desired_name = NameDialog(self.root).show()
        if desired_name is None:
            self._on_close()
            return

        if not self._safe_send({"type": "join", "requested_name": desired_name}):
            return

        self.root.after(50, self._process_network_events)
        self.root.mainloop()

    def _configure_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Accent.TButton",
            font=(FONT_FAMILY, 10, "bold"),
            foreground="#FFFFFF",
            background=ACCENT,
            borderwidth=0,
            padding=(16, 9),
        )
        style.map(
            "Accent.TButton",
            background=[("active", ACCENT_ACTIVE), ("disabled", "#AAB7E8")],
            foreground=[("disabled", "#F3F5F7")],
        )

        style.configure(
            "Secondary.TButton",
            font=(FONT_FAMILY, 10),
            foreground=TEXT,
            background=SURFACE,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            borderwidth=1,
            padding=(14, 8),
        )
        style.map("Secondary.TButton", background=[("active", "#F2F4F7")])

        style.configure(
            "Chat.TEntry",
            font=(FONT_FAMILY, 10),
            foreground=TEXT,
            fieldbackground=ENTRY_BG,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=9,
        )
        style.map("Chat.TEntry", bordercolor=[("focus", ACCENT)])

    def _build_ui(self):
        header = tk.Frame(self.root, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        header.pack(fill="x")

        header_inner = tk.Frame(header, bg=SURFACE, padx=24, pady=14)
        header_inner.pack(fill="x")

        title_group = tk.Frame(header_inner, bg=SURFACE)
        title_group.pack(side="left")

        tk.Label(
            title_group,
            text="Sala de chat",
            bg=SURFACE,
            fg=TEXT,
            font=(FONT_FAMILY, 17, "bold"),
        ).pack(anchor="w")

        status_row = tk.Frame(title_group, bg=SURFACE)
        status_row.pack(anchor="w", pady=(3, 0))

        self.status_dot = tk.Label(
            status_row,
            text="●",
            bg=SURFACE,
            fg=MUTED,
            font=(FONT_FAMILY, 8),
        )
        self.status_dot.pack(side="left", padx=(0, 6))

        self.status_label = tk.Label(
            status_row,
            text="Desconectado",
            bg=SURFACE,
            fg=MUTED,
            font=(FONT_FAMILY, 9),
        )
        self.status_label.pack(side="left")

        self.history_button = ttk.Button(
            header_inner,
            text="Recuperar historial",
            command=self._request_history,
            state="disabled",
            style="Secondary.TButton",
        )
        self.history_button.pack(side="right")

        content = tk.Frame(self.root, bg=APP_BG, padx=18, pady=18)
        content.pack(fill="both", expand=True)
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        chat_panel = tk.Frame(
            content,
            bg=SURFACE,
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        chat_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        chat_panel.grid_rowconfigure(0, weight=1)
        chat_panel.grid_columnconfigure(0, weight=1)

        self.chat_box = ScrolledText(
            chat_panel,
            wrap="word",
            state="disabled",
            bg=SURFACE,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            borderwidth=0,
            padx=18,
            pady=18,
            font=(FONT_FAMILY, 10),
            spacing1=2,
            spacing3=8,
        )
        self.chat_box.grid(row=0, column=0, sticky="nsew")
        self.chat_box.tag_config("timestamp", foreground=MUTED, font=(FONT_FAMILY, 8))
        self.chat_box.tag_config("body", foreground=TEXT, font=(FONT_FAMILY, 10))
        self.chat_box.tag_config(
            "system",
            foreground=SYSTEM,
            font=(FONT_FAMILY, 9, "italic"),
            justify="center",
            spacing1=4,
            spacing3=8,
        )
        self.chat_box.tag_config("self_marker", foreground=MUTED, font=(FONT_FAMILY, 8))

        composer = tk.Frame(chat_panel, bg=SURFACE, padx=14, pady=12)
        composer.grid(row=1, column=0, sticky="ew")
        composer.grid_columnconfigure(0, weight=1)

        self.message_entry = ttk.Entry(composer, style="Chat.TEntry")
        self.message_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.message_entry.bind("<Return>", self._send_from_event)

        self.send_button = ttk.Button(
            composer,
            text="Enviar",
            command=self._send_message,
            state="disabled",
            style="Accent.TButton",
        )
        self.send_button.grid(row=0, column=1)

        tk.Label(
            composer,
            text="Enter para enviar  ·  /history también recupera el historial",
            bg=SURFACE,
            fg=MUTED,
            font=(FONT_FAMILY, 8),
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(7, 0))

        sidebar = tk.Frame(
            content,
            bg=SURFACE,
            width=215,
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        sidebar.grid(row=0, column=1, sticky="ns")
        sidebar.grid_propagate(False)

        side_header = tk.Frame(sidebar, bg=SURFACE, padx=16, pady=16)
        side_header.pack(fill="x")

        tk.Label(
            side_header,
            text="En línea",
            bg=SURFACE,
            fg=TEXT,
            font=(FONT_FAMILY, 11, "bold"),
        ).pack(side="left")

        self.online_count_label = tk.Label(
            side_header,
            text="—",
            bg="#EEF2FF",
            fg=ACCENT,
            font=(FONT_FAMILY, 9, "bold"),
            padx=7,
            pady=2,
        )
        self.online_count_label.pack(side="right")

        self.participants_box = tk.Text(
            sidebar,
            state="disabled",
            bg=SURFACE,
            fg=TEXT,
            relief="flat",
            borderwidth=0,
            padx=16,
            pady=2,
            width=22,
            font=(FONT_FAMILY, 10),
            cursor="arrow",
        )
        self.participants_box.pack(fill="both", expand=True)

        self.presence_hint = tk.Label(
            sidebar,
            text="Esperando información\nde presencia del servidor",
            bg=SURFACE,
            fg=MUTED,
            justify="left",
            font=(FONT_FAMILY, 8),
            padx=16,
            pady=14,
        )
        self.presence_hint.pack(fill="x", side="bottom")

        self._append_system("Conecta con el servidor y elige un nombre para comenzar.")

    def _send_from_event(self, _event):
        self._send_message()
        return "break"

    def _send_message(self):
        if not self.connected or not self.join_accepted:
            return

        text = self.message_entry.get().strip()
        if not text:
            return

        self.message_entry.delete(0, tk.END)

        if text == "/history":
            self._request_history()
            return

        self._safe_send({"type": "chat", "text": text})

        # No se dibuja el mensaje aquí. Esperamos el evento "message" del
        # servidor para que todos los clientes compartan el mismo orden.

    def _request_history(self):
        if not self.connected or not self.join_accepted:
            return

        if self._safe_send({"type": "history_request"}):
            self._append_system("Historial solicitado al servidor.")

    def _safe_send(self, message):
        try:
            self.network.send(message)
            return True
        except (ConnectionError, OSError) as exc:
            self._append_system(f"No se pudo enviar: {exc}")
            return False

    def _process_network_events(self):
        while True:
            try:
                message = self.incoming_queue.get_nowait()
            except queue.Empty:
                break
            self._handle_server_message(message)

        if self.root.winfo_exists():
            self.root.after(50, self._process_network_events)

    def _handle_server_message(self, message):
        message_type = message.get("type")

        if message_type == "join_ok":
            self.username = message.get("assigned_name", "usuario")
            self.join_accepted = True
            self._set_connection_state(
                "connected",
                f"{self.username}  ·  {self.host}:{self.port}",
            )
            self._append_system(f"Nombre asignado por el servidor: {self.username}")
            self.send_button.config(state="normal")
            self.history_button.config(state="normal")
            self.message_entry.focus_set()
            return

        if message_type == "message":
            self._display_message_event(message)
            return

        if message_type == "history":
            messages = message.get("messages", [])
            for item in messages:
                message_id = item.get("id")
                if message_id is None:
                    continue
                self.message_cache[message_id] = item

            self._render_cached_messages()
            self._append_system(f"Historial recuperado: {len(messages)} mensajes recibidos.")
            return

        if message_type == "presence":
            self._update_presence(message.get("users", []), message.get("count"))
            return

        if message_type == "system":
            self._append_system(message.get("message", ""))
            return

        if message_type == "error":
            self._append_system(f"Error del servidor: {message.get('message', 'desconocido')}")
            return

        if message_type == "connection_lost":
            self.connected = False
            self.join_accepted = False
            self.send_button.config(state="disabled")
            self.history_button.config(state="disabled")
            self._set_connection_state("error", "Conexión perdida")
            self._append_system(f"Conexión perdida: {message.get('message', '')}")
            return

        if message_type == "local_error":
            self._append_system(message.get("message", "Error local."))
            return

        self._append_system(f"Mensaje no reconocido del servidor: {message}")

    def _display_message_event(self, message):
        message_id = message.get("id")

        if message_id is None:
            self.messages_without_id.append(message)
            self._append_chat_message(
                sender=message.get("sender", "?"),
                text=message.get("text", ""),
                timestamp=message.get("timestamp", "--:--:--"),
            )
            return

        if message_id in self.message_cache:
            return

        self.message_cache[message_id] = message
        self._append_chat_message(
            sender=message.get("sender", "?"),
            text=message.get("text", ""),
            timestamp=message.get("timestamp", "--:--:--"),
        )

    def _render_cached_messages(self):
        """Reconstruye mensajes de chat en orden por ID tras pedir historial."""
        self.chat_box.config(state="normal")
        self.chat_box.delete("1.0", tk.END)
        self.chat_box.config(state="disabled")

        for message_id in sorted(self.message_cache):
            item = self.message_cache[message_id]
            self._append_chat_message(
                sender=item.get("sender", "?"),
                text=item.get("text", ""),
                timestamp=item.get("timestamp", "--:--:--"),
            )

        for item in self.messages_without_id:
            self._append_chat_message(
                sender=item.get("sender", "?"),
                text=item.get("text", ""),
                timestamp=item.get("timestamp", "--:--:--"),
            )

    def _append_chat_message(self, sender, text, timestamp):
        color = self._color_for_name(sender)
        tag_name = f"user_{hashlib.sha256(sender.encode('utf-8')).hexdigest()}"

        self.chat_box.config(state="normal")

        if tag_name not in self.chat_box.tag_names():
            self.chat_box.tag_config(
                tag_name,
                foreground=color,
                font=(FONT_FAMILY, 10, "bold"),
            )

        display_time = self._short_time(timestamp)
        self.chat_box.insert(tk.END, f"{display_time}  ", "timestamp")
        self.chat_box.insert(tk.END, sender, tag_name)

        if sender == self.username:
            self.chat_box.insert(tk.END, "  tú", "self_marker")

        self.chat_box.insert(tk.END, "\n")
        self.chat_box.insert(tk.END, f"{text}\n", "body")
        self.chat_box.see(tk.END)
        self.chat_box.config(state="disabled")

    def _append_system(self, text):
        if not hasattr(self, "chat_box"):
            return

        self.chat_box.config(state="normal")
        self.chat_box.insert(tk.END, f"{text}\n", "system")
        self.chat_box.see(tk.END)
        self.chat_box.config(state="disabled")

    def _update_presence(self, users, count=None):
        clean_users = [str(user) for user in users]
        self.participants = sorted(clean_users, key=str.casefold)
        shown_count = len(self.participants) if count is None else count

        self.online_count_label.config(text=str(shown_count))
        self.presence_hint.pack_forget()

        self.participants_box.config(state="normal")
        self.participants_box.delete("1.0", tk.END)

        for name in self.participants:
            tag_name = f"presence_{hashlib.sha256(name.encode('utf-8')).hexdigest()}"
            if tag_name not in self.participants_box.tag_names():
                self.participants_box.tag_config(
                    tag_name,
                    foreground=self._color_for_name(name),
                    font=(FONT_FAMILY, 10, "bold"),
                )

            self.participants_box.insert(tk.END, "● ", tag_name)
            self.participants_box.insert(tk.END, name, tag_name)
            if name == self.username:
                self.participants_box.insert(tk.END, "  (tú)", "presence_self")
            self.participants_box.insert(tk.END, "\n\n")

        self.participants_box.tag_config(
            "presence_self",
            foreground=MUTED,
            font=(FONT_FAMILY, 8),
        )
        self.participants_box.config(state="disabled")

    def _set_connection_state(self, state, text):
        color = {
            "connected": SUCCESS,
            "connecting": "#D18B19",
            "error": DANGER,
        }.get(state, MUTED)
        self.status_dot.config(fg=color)
        self.status_label.config(text=text)

    @staticmethod
    def _short_time(timestamp):
        value = str(timestamp)
        if " " in value:
            return value.rsplit(" ", 1)[-1]
        return value

    @staticmethod
    def _color_for_name(name):
        """Mismo nombre -> mismo color; Ana, Ana2, Ana3 -> colores distintos."""
        match = re.fullmatch(r"(.*?)(\d+)?", name)
        base_name = match.group(1) if match else name
        suffix_text = match.group(2) if match else None

        digest = hashlib.sha256(base_name.encode("utf-8")).digest()
        base_index = int.from_bytes(digest[:4], byteorder="big") % len(NAME_COLORS)

        if suffix_text is None:
            offset = 0
        else:
            suffix = int(suffix_text)
            offset = max(suffix - 1, 0)

        return NAME_COLORS[(base_index + offset) % len(NAME_COLORS)]

    def _on_close(self):
        if self.connected:
            try:
                self.network.send({"type": "leave"})
            except (ConnectionError, OSError):
                pass

        self.connected = False
        self.join_accepted = False
        self.network.close()

        if self.root.winfo_exists():
            self.root.destroy()
