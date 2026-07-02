import csv
import json
import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime
import serial.tools.list_ports
from pymodbus.client import ModbusSerialClient, ModbusTcpClient

import customtkinter as ctk

from scanner.models import DeviceResult, ScanConfig, Protocol, BAUD_RATES, FUNCTION_CODES
from scanner.worker import ScanWorker
from ui import theme as th

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FindMyModbus - Modbus Device Scanner")
        self.geometry("1140x800")
        self.minsize(860, 640)
        self.configure(fg_color=th.BG_BASE)
        self.results: list[DeviceResult] = []
        self.worker = ScanWorker()
        self.serial_client: ModbusSerialClient | None = None

        self._build_ui()
        self._refresh_ports()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Build UI ─────────────────────────────────────────────
    def _build_ui(self):
        # Shell: un margen exterior generoso para que las tarjetas "floten"
        # sobre el fondo, en vez de pegarse a los bordes de la ventana.
        shell = ctk.CTkFrame(self, fg_color=th.TRANSPARENT)
        shell.pack(fill="both", expand=True, padx=16, pady=16)

        self._build_header(shell)

        # Tarjeta: Conexión (tabs RTU / TCP / Guide)
        conn_card = th.glass_card(shell, level=0)
        conn_card.pack(fill="x", pady=(0, th.PAD_GAP))

        self.tabview = ctk.CTkTabview(
            conn_card,
            anchor="nw",
            fg_color=th.GLASS_1,
            corner_radius=th.RADIUS_CARD - 4,
            border_width=1,
            border_color=th.BORDER_SOFT,
            segmented_button_fg_color=th.GLASS_0,
            segmented_button_selected_color=th.GLASS_ACTIVE,
            segmented_button_selected_hover_color=th.GLASS_ACTIVE,
            segmented_button_unselected_color=th.GLASS_0,
            segmented_button_unselected_hover_color=th.GLASS_HOVER,
            text_color=th.TEXT_PRIMARY,
            text_color_disabled=th.TEXT_MUTED,
        )
        self.tabview.pack(fill="x", padx=th.PAD_CARD, pady=th.PAD_CARD)

        self.tab_rtu = self.tabview.add("RTU")
        self.tab_tcp = self.tabview.add("TCP")
        self.tab_guide = self.tabview.add("Guide")
        self._build_rtu_tab(self.tab_rtu)
        self._build_tcp_tab(self.tab_tcp)
        self._build_guide_tab(self.tab_guide)

        self._build_scan_controls(shell)
        self._build_status_block(shell)

        # Tarjeta: tabla de resultados + barra de exportación
        results_card = th.glass_card(shell, level=0)
        results_card.pack(fill="both", expand=True)
        results_card.grid_rowconfigure(0, weight=1)
        results_card.grid_columnconfigure(0, weight=1)

        self._build_results_table(results_card)
        self._build_export_bar(results_card)

    # ── Header ───────────────────────────────────────────────
    def _build_header(self, parent):
        header = ctk.CTkFrame(parent, fg_color=th.TRANSPARENT)
        header.pack(fill="x", pady=(0, th.PAD_GAP))

        # Marca de agua/glifo simple, sin depender de íconos externos.
        glyph = ctk.CTkLabel(
            header, text="◐", font=th.font(22), text_color=th.TEXT_SECONDARY,
            width=36, height=36, fg_color=th.GLASS_0, corner_radius=th.RADIUS_CTRL,
        )
        glyph.pack(side="left", padx=(0, 12))

        title_box = ctk.CTkFrame(header, fg_color=th.TRANSPARENT)
        title_box.pack(side="left", fill="y")
        ctk.CTkLabel(
            title_box, text="FindMyModbus", font=th.font(19, "bold"),
            text_color=th.TEXT_PRIMARY, anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box, text=th.eyebrow("Modbus Device Scanner"), font=th.font(11),
            text_color=th.TEXT_MUTED, anchor="w",
        ).pack(anchor="w")

    # ── RTU tab ──────────────────────────────────────────────
    def _build_rtu_tab(self, parent):
        f = ctk.CTkFrame(parent, fg_color=th.TRANSPARENT)
        f.pack(fill="x", padx=6, pady=6)

        ctk.CTkLabel(f, text="Port:", text_color=th.TEXT_SECONDARY).grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")
        self.port_combo = ctk.CTkComboBox(f, values=["(detecting...)"], width=220, **th.style_combo())
        self.port_combo.grid(row=0, column=1, padx=(0, 5), pady=5, sticky="w")
        ctk.CTkButton(f, text="\u27f3", width=30, command=self._refresh_ports, **th.style_button()).grid(row=0, column=2, padx=(0, 15), pady=5)

        ctk.CTkLabel(f, text="Baudrate:", text_color=th.TEXT_SECONDARY).grid(row=0, column=3, padx=(0, 5), pady=5, sticky="w")
        self.baud_var = ctk.StringVar(value="9600")
        ctk.CTkComboBox(f, values=[str(b) for b in BAUD_RATES], variable=self.baud_var, width=90, **th.style_combo()).grid(
            row=0, column=4, padx=(0, 15), pady=5, sticky="w"
        )

        ctk.CTkLabel(f, text="Parity:", text_color=th.TEXT_SECONDARY).grid(row=0, column=5, padx=(0, 5), pady=5, sticky="w")
        self.parity_var = ctk.StringVar(value="N")
        ctk.CTkComboBox(f, values=["N", "E", "O"], variable=self.parity_var, width=60, **th.style_combo()).grid(
            row=0, column=6, padx=(0, 15), pady=5, sticky="w"
        )

        self.auto_baud_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            f, text="Auto-baud", variable=self.auto_baud_var,
            progress_color=th.ACCENT_SOFT, button_color=th.TEXT_PRIMARY,
            button_hover_color=th.TEXT_PRIMARY, fg_color=th.GLASS_2,
            text_color=th.TEXT_SECONDARY,
        ).grid(row=0, column=7, padx=(0, 5), pady=5, sticky="w")

        conn_frame = ctk.CTkFrame(f, fg_color=th.TRANSPARENT)
        conn_frame.grid(row=1, column=0, columnspan=8, pady=(8, 5), sticky="ew")

        self.btn_connect = ctk.CTkButton(
            conn_frame, text="Connect", command=self._rtu_connect, width=100,
            **th.style_button(),
        )
        self.btn_connect.pack(side="left", padx=(0, 10))

        led_wrap = ctk.CTkFrame(conn_frame, fg_color=th.GLASS_2, corner_radius=th.RADIUS_PILL, width=16, height=16)
        led_wrap.pack(side="left", padx=(0, 5))
        led_wrap.pack_propagate(False)
        self.led_canvas = tk.Canvas(led_wrap, width=16, height=16, highlightthickness=0, bg=th.GLASS_2)
        self.led_canvas.pack(fill="both", expand=True)
        self._set_led(False)

        self.conn_status_var = ctk.StringVar(value="Disconnected")
        ctk.CTkLabel(conn_frame, textvariable=self.conn_status_var, font=th.font(12), text_color=th.TEXT_SECONDARY).pack(side="left")

    def _set_led(self, on: bool):
        self.led_canvas.delete("all")
        color = th.STATE_OK if on else th.STATE_OFF
        self.led_canvas.create_oval(2, 2, 14, 14, fill=color, outline=th.BORDER_STRONG)

    def _refresh_ports(self):
        try:
            ports = serial.tools.list_ports.comports()
            items = [f"{p.device} - {p.description}" if p.description else p.device for p in sorted(ports, key=lambda x: x.device)]
            if not items:
                items = ["(no ports found)"]
            self.port_combo.configure(values=items)
            if items[0] != "(no ports found)":
                self.port_combo.set(items[0])
        except Exception:
            self.port_combo.configure(values=["(error detecting ports)"])

    def _rtu_connect(self):
        if self.serial_client is not None:
            self._rtu_disconnect()
            return

        raw = self.port_combo.get()
        port = raw.split(" - ")[0] if " - " in raw else raw
        if port.startswith("("):
            self.status_var.set(f"No valid port selected: {raw}")
            return

        baud = int(self.baud_var.get())
        parity = self.parity_var.get()
        client = ModbusSerialClient(
            port=port, baudrate=baud, bytesize=8,
            parity=parity, stopbits=1, timeout=0.5,
        )
        if client.connect():
            self.serial_client = client
            self._set_led(True)
            self.conn_status_var.set(f"Connected @ {baud}")
            self.btn_connect.configure(text="Disconnect")
            self.status_var.set(f"Connected to {port} @ {baud}")
        else:
            client.close()
            self.status_var.set(f"Failed to connect to {port} @ {baud}")

    def _rtu_disconnect(self):
        if self.serial_client:
            try:
                self.serial_client.close()
            except Exception:
                pass
            self.serial_client = None
        self._set_led(False)
        self.conn_status_var.set("Disconnected")
        self.btn_connect.configure(text="Connect")
        self.status_var.set("Disconnected")

    # ── TCP tab ──────────────────────────────────────────────
    def _build_tcp_tab(self, parent):
        f = ctk.CTkFrame(parent, fg_color=th.TRANSPARENT)
        f.pack(fill="x", padx=6, pady=6)

        ctk.CTkLabel(f, text="Host:", text_color=th.TEXT_SECONDARY).grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")
        self.host_var = ctk.StringVar(value="192.168.1.100")
        ctk.CTkEntry(f, textvariable=self.host_var, width=150, **th.style_entry()).grid(row=0, column=1, padx=(0, 15), pady=5, sticky="w")

        ctk.CTkLabel(f, text="Port:", text_color=th.TEXT_SECONDARY).grid(row=0, column=2, padx=(0, 5), pady=5, sticky="w")
        self.tcp_port_var = ctk.StringVar(value="502")
        ctk.CTkEntry(f, textvariable=self.tcp_port_var, width=70, **th.style_entry()).grid(row=0, column=3, padx=(0, 15), pady=5, sticky="w")

        ctk.CTkButton(f, text="Test TCP", command=self._tcp_test, width=100, **th.style_button()).grid(
            row=1, column=0, columnspan=4, pady=(8, 5), sticky="w"
        )

    def _tcp_test(self):
        host = self.host_var.get()
        port = int(self.tcp_port_var.get())
        client = ModbusTcpClient(host, port=port, timeout=2)
        if client.connect():
            client.close()
            self.status_var.set(f"TCP connection to {host}:{port} OK")
        else:
            self.status_var.set(f"TCP connection to {host}:{port} FAILED")

    # ── Guide tab ────────────────────────────────────────────
    def _build_guide_tab(self, parent):
        f = ctk.CTkScrollableFrame(
            parent, fg_color=th.TRANSPARENT,
            scrollbar_button_color=th.GLASS_2,
            scrollbar_button_hover_color=th.GLASS_HOVER,
        )
        f.pack(fill="both", expand=True, padx=6, pady=6)

        sections = [
            ("Wiring -- USB-485 to Modbus RTU bus", """\
  USB-485 dongle                Bus RS-485
  -----------------             ------------------
    A (D+) ---------------------- A --- A(slave1) --- A(slave2) ...
    B (D-) ---------------------- B --- B(slave1) --- B(slave2) ...
    GND   ---------------------- GND (recommended)

  . Use twisted-pair shielded cable
  . Maximum distance: ~1200 m @ 9600 baud"""),

            ("Termination resistor", """\
  . 120 Ohm resistor between A and B at BOTH ends of the bus
  . The USB-485 dongle usually has a jumper/switch to enable it
  . Only enable at physical ends -- never in the middle"""),

            ("Fail-safe biasing", """\
  . Pull A (D+) to 3.3V/5V via 680 Ohm resistor
  . Pull B (D-) to GND via 680 Ohm resistor
  . Keeps bus in known-idle state when no device is driving it
  . Many USB-485 dongles include this onboard"""),

            ("Troubleshooting", """\
  Problem                    Likely fix
  -----------------------------------------------------
  No response from any slave -> Check A/B polarity (swap them)
  Some slaves respond        -> Check termination (ends only)
  Intermittent reads         -> Lower baudrate / check shielding
  Timeout on every slave     -> Verify GND connection
  Only one slave responds    -> Wrong slave ID or duplicate IDs
  Noise / garbage values     -> Add TVS / use shorter cable
"""),

            ("Connection checklist", """\
  [ ] A / B wired correctly (not reversed)
  [ ] GND connected between dongle and bus
  [ ] Termination 120 Ohm enabled at bus ends
  [ ] Baudrate matches the slowest device on bus
  [ ] Parity and stop bits match all devices
  [ ] Each device has a unique slave ID (1-247)"""),
        ]

        for title, body in sections:
            card = th.glass_card(f, level=1, border_color=th.BORDER_SOFT)
            card.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(
                card, text=th.eyebrow(title), font=th.font(11, "bold"),
                text_color=th.TEXT_SECONDARY, anchor="w",
            ).pack(fill="x", padx=14, pady=(12, 4))
            ctk.CTkLabel(
                card, text=body, font=th.mono(12), text_color=th.TEXT_PRIMARY,
                anchor="w", justify="left",
            ).pack(fill="x", padx=14, pady=(0, 12))

    # ── Scan controls ────────────────────────────────────────
    def _build_scan_controls(self, parent):
        card = th.glass_card(parent, level=0)
        card.pack(fill="x", pady=(0, th.PAD_GAP))

        f = ctk.CTkFrame(card, fg_color=th.TRANSPARENT)
        f.pack(fill="x", padx=th.PAD_CARD, pady=th.PAD_CARD)

        ctk.CTkLabel(f, text=th.eyebrow("Scan parameters"), font=th.font(11, "bold"), text_color=th.TEXT_MUTED).grid(
            row=0, column=0, columnspan=9, sticky="w", pady=(0, 8)
        )

        ctk.CTkLabel(f, text="Slave range:", text_color=th.TEXT_SECONDARY).grid(row=1, column=0, padx=(0, 5), pady=5, sticky="w")
        self.slave_start_var = ctk.StringVar(value="1")
        ctk.CTkEntry(f, textvariable=self.slave_start_var, width=50, **th.style_entry()).grid(row=1, column=1, padx=(0, 5), pady=5, sticky="w")
        ctk.CTkLabel(f, text="to", text_color=th.TEXT_MUTED).grid(row=1, column=2, padx=(0, 5), pady=5)
        self.slave_end_var = ctk.StringVar(value="247")
        ctk.CTkEntry(f, textvariable=self.slave_end_var, width=50, **th.style_entry()).grid(row=1, column=3, padx=(0, 15), pady=5, sticky="w")

        ctk.CTkLabel(f, text="Regs/slave:", text_color=th.TEXT_SECONDARY).grid(row=1, column=4, padx=(0, 5), pady=5, sticky="w")
        self.regs_var = ctk.StringVar(value="10")
        ctk.CTkEntry(f, textvariable=self.regs_var, width=50, **th.style_entry()).grid(row=1, column=5, padx=(0, 15), pady=5, sticky="w")

        ctk.CTkLabel(f, text="Timeout (s):", text_color=th.TEXT_SECONDARY).grid(row=1, column=6, padx=(0, 5), pady=5, sticky="w")
        self.timeout_var = ctk.StringVar(value="0.3")
        ctk.CTkEntry(f, textvariable=self.timeout_var, width=50, **th.style_entry()).grid(row=1, column=7, padx=(0, 15), pady=5, sticky="w")

        fc_frame = ctk.CTkFrame(f, fg_color=th.TRANSPARENT)
        fc_frame.grid(row=2, column=0, columnspan=6, pady=(10, 5), sticky="w")
        ctk.CTkLabel(fc_frame, text="Functions:", text_color=th.TEXT_SECONDARY).pack(side="left", padx=(0, 8))
        self.fc_vars = {}
        for code, name in FUNCTION_CODES.items():
            var = ctk.BooleanVar(value=True)
            self.fc_vars[code] = var
            ctk.CTkSwitch(
                fc_frame, text=name.split(" (")[0], variable=var,
                progress_color=th.ACCENT_SOFT, button_color=th.TEXT_PRIMARY,
                button_hover_color=th.TEXT_PRIMARY, fg_color=th.GLASS_2,
                text_color=th.TEXT_SECONDARY,
            ).pack(side="left", padx=5)

        self.btn_scan = ctk.CTkButton(
            f, text="\u25b6  Start Scan", command=self._start_scan,
            **th.style_button(fg_color="#2a3a30", hover_color="#33463b", border_color="#3a4d40", text_color=th.TEXT_PRIMARY),
        )
        self.btn_scan.grid(row=3, column=6, padx=(0, 5), pady=(10, 0), sticky="e")
        self.btn_stop = ctk.CTkButton(
            f, text="\u23f9  Stop", command=self._stop_scan,
            **th.style_button(fg_color="#3a2a2a", hover_color="#4a3333", border_color="#4d3a3a", text_color=th.TEXT_PRIMARY),
            state="disabled",
        )
        self.btn_stop.grid(row=3, column=7, padx=(0, 5), pady=(10, 0), sticky="w")
        ctk.CTkButton(f, text="Clear", command=self._clear_results, **th.style_button()).grid(
            row=3, column=8, padx=(0, 5), pady=(10, 0), sticky="w"
        )

        f.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8), weight=0)

    # ── Progress + status ────────────────────────────────────
    def _build_status_block(self, parent):
        block = ctk.CTkFrame(parent, fg_color=th.TRANSPARENT)
        block.pack(fill="x", pady=(0, th.PAD_GAP))

        self.progress_bar = ctk.CTkProgressBar(
            block, fg_color=th.GLASS_0, progress_color=th.ACCENT,
            corner_radius=th.RADIUS_PILL, height=8, border_width=1, border_color=th.BORDER_SOFT,
        )
        self.progress_bar.pack(fill="x", pady=(0, 6))
        self.progress_bar.set(0)

        self.status_var = ctk.StringVar(value="Ready")
        self.status_label = ctk.CTkLabel(
            block, textvariable=self.status_var, anchor="w", font=th.font(12), text_color=th.TEXT_SECONDARY,
        )
        self.status_label.pack(fill="x")

    # ── Results table ────────────────────────────────────────
    def _build_results_table(self, parent):
        container = ctk.CTkFrame(parent, fg_color=th.TRANSPARENT)
        container.grid(row=0, column=0, sticky="nsew", padx=th.PAD_CARD, pady=(th.PAD_CARD, 8))
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            container, text=th.eyebrow("Results"), font=th.font(11, "bold"), text_color=th.TEXT_MUTED,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        cols = ("slave_id", "function", "address", "value", "protocol", "baudrate", "connection", "timestamp")
        headers = {"slave_id": "Slave", "function": "Func", "address": "Addr", "value": "Value",
                   "protocol": "Proto", "baudrate": "Baud", "connection": "Connection", "timestamp": "Time"}

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=th.TABLE_BG, foreground=th.TEXT_PRIMARY, fieldbackground=th.TABLE_BG,
                        borderwidth=0, relief="flat", rowheight=28, font=(th.FONT_FAMILY, 12))
        style.configure("Treeview.Heading",
                        background=th.TABLE_HEADER_BG, foreground=th.TEXT_SECONDARY, borderwidth=0, relief="flat",
                        font=(th.FONT_FAMILY, 12, "bold"))
        style.map("Treeview.Heading", background=[("active", th.TABLE_HEADER_BG)])
        style.map("Treeview", background=[("selected", th.TABLE_SEL)], foreground=[("selected", th.TEXT_PRIMARY)])
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        style.configure("Glass.Vertical.TScrollbar",
                        background=th.GLASS_2, troughcolor=th.GLASS_0,
                        bordercolor=th.BORDER_SOFT, arrowcolor=th.TEXT_SECONDARY, relief="flat")
        style.map("Glass.Vertical.TScrollbar", background=[("active", th.GLASS_HOVER)])

        self.tree = ttk.Treeview(container, columns=cols, show="headings", height=15, style="Treeview")
        for col in cols:
            self.tree.heading(col, text=headers[col], anchor="w")
            self.tree.column(col, width=70, anchor="w", minwidth=50)
        self.tree.column("value", width=80)
        self.tree.column("connection", width=140)
        self.tree.column("timestamp", width=160)
        self.tree.column("slave_id", width=65)

        self.tree.tag_configure("even", background=th.TABLE_BG)
        self.tree.tag_configure("odd", background=th.TABLE_ROW_ALT)

        vsb = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview, style="Glass.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")

    # ── Export bar ───────────────────────────────────────────
    def _build_export_bar(self, parent):
        f = ctk.CTkFrame(parent, fg_color=th.TRANSPARENT)
        f.grid(row=1, column=0, sticky="ew", padx=th.PAD_CARD, pady=(0, th.PAD_CARD))
        ctk.CTkButton(f, text="Export CSV", command=lambda: self._export("csv"), **th.style_button()).pack(side="left", padx=(0, 5))
        ctk.CTkButton(f, text="Export JSON", command=lambda: self._export("json"), **th.style_button()).pack(side="left")

    # ── Config & scan ────────────────────────────────────────
    def _get_config(self) -> ScanConfig:
        is_rtu = self.tabview.get() == "RTU"
        if is_rtu:
            raw = self.port_combo.get()
            port = raw.split(" - ")[0] if " - " in raw else raw
            return ScanConfig(
                protocol=Protocol.RTU,
                port=port,
                baudrate=int(self.baud_var.get()),
                parity=self.parity_var.get(),
                stopbits=1,
                auto_baud=self.auto_baud_var.get(),
                slave_start=int(self.slave_start_var.get()),
                slave_end=int(self.slave_end_var.get()),
                function_codes=[c for c, v in self.fc_vars.items() if v.get()],
                registers_per_slave=int(self.regs_var.get()),
                timeout=float(self.timeout_var.get()),
            )
        return ScanConfig(
            protocol=Protocol.TCP,
            host=self.host_var.get(),
            tcp_port=int(self.tcp_port_var.get()),
            slave_start=int(self.slave_start_var.get()),
            slave_end=int(self.slave_end_var.get()),
            function_codes=[c for c, v in self.fc_vars.items() if v.get()],
            registers_per_slave=int(self.regs_var.get()),
            timeout=float(self.timeout_var.get()),
        )

    def _start_scan(self):
        if self.worker.is_running:
            return
        is_rtu = self.tabview.get() == "RTU"
        auto_baud = self.auto_baud_var.get()
        if is_rtu and self.serial_client and not auto_baud:
            self.status_var.set("Scanning with persistent connection...")
        elif is_rtu and self.serial_client and auto_baud:
            self.status_var.set("Auto-baud active -- will reconnect at each baudrate")

        self.results.clear()
        self._clear_table()
        self.btn_scan.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.progress_bar.set(0)
        config = self._get_config()
        existing = self.serial_client if is_rtu else None
        self.worker.start(config, self._on_result, self._on_progress, existing)

    def _stop_scan(self):
        self.worker.stop()
        self.btn_scan.configure(state="normal")
        self.btn_stop.configure(state="disabled")

    def _on_result(self, result: DeviceResult):
        self.after(0, self._add_result_row, result)

    def _add_result_row(self, result: DeviceResult):
        self.results.append(result)
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        tag = "even" if len(self.results) % 2 == 0 else "odd"
        self.tree.insert("", "end", values=(
            result.slave_id, result.function_code, result.address, result.value,
            result.protocol.value, result.baudrate or "", result.connection, ts,
        ), tags=(tag,))

    def _on_progress(self, pct, status):
        self.after(0, self._update_progress, pct, status)

    def _update_progress(self, pct, status):
        self.progress_bar.set(pct)
        self.status_var.set(status)
        if pct >= 1.0:
            self.btn_scan.configure(state="normal")
            self.btn_stop.configure(state="disabled")
            self.status_var.set(f"Done - {len(self.results)} registers found")

    def _clear_results(self):
        self.results.clear()
        self._clear_table()
        self.progress_bar.set(0)
        self.status_var.set("Ready")

    def _clear_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _export(self, fmt: str):
        if not self.results:
            self.status_var.set("No results to export")
            return
        ext = ".csv" if fmt == "csv" else ".json"
        fp = filedialog.asksaveasfilename(defaultextension=ext, filetypes=[(fmt.upper(), f"*{ext}")])
        if not fp:
            return

        data = [
            {
                "slave_id": r.slave_id, "function_code": r.function_code,
                "address": r.address, "value": r.value, "protocol": r.protocol.value,
                "baudrate": r.baudrate, "connection": r.connection,
            }
            for r in self.results
        ]
        if fmt == "csv":
            with open(fp, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=data[0].keys())
                w.writeheader()
                w.writerows(data)
        else:
            with open(fp, "w") as f:
                json.dump(data, f, indent=2)
        self.status_var.set(f"Exported {len(data)} records to {fp}")

    def _on_close(self):
        self._rtu_disconnect()
        self.worker.stop()
        self.destroy()
