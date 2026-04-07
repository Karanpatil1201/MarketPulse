# ============================================================
# ui.py — Full Tkinter UI (Groww-inspired dark dashboard)
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading

from config import (
    APP_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT,
    BG_DARK, BG_CARD, BG_SIDEBAR, BG_INPUT,
    ACCENT_GREEN, ACCENT_RED, ACCENT_BLUE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER_COLOR, CHART_BG,
    FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_BODY_BOLD,
    FONT_SMALL, FONT_PRICE, STOCKS, MAX_TRANSACTION
)
from engine   import PriceEngine, StockData
from portfolio import Portfolio


# ── Helper: styled Label factory ─────────────────────────────
def lbl(parent, text="", fg=TEXT_PRIMARY, font=FONT_BODY,
        bg=None, anchor="w", **kw):
    bg = bg or parent["bg"]
    return tk.Label(parent, text=text, fg=fg, font=font,
                    bg=bg, anchor=anchor, **kw)


# ── Helper: styled Button factory ────────────────────────────
def btn(parent, text, command, color=ACCENT_BLUE, fg=BG_DARK,
        width=10, **kw):
    return tk.Button(
        parent, text=text, command=command,
        bg=color, fg=fg, font=FONT_BODY_BOLD,
        relief="flat", bd=0, cursor="hand2",
        activebackground=color, activeforeground=fg,
        width=width, pady=6, **kw
    )


# ── Helper: horizontal separator ─────────────────────────────
def sep(parent, color=BORDER_COLOR):
    tk.Frame(parent, bg=color, height=1).pack(fill="x", pady=4)


# =============================================================
class App(tk.Tk):
    """Root application window."""

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(True, True)
        self.configure(bg=BG_DARK)
        self.minsize(1100, 680)

        # Core objects
        self.engine    = PriceEngine()
        self.portfolio = Portfolio()

        # State
        self._selected_symbol = list(STOCKS.keys())[0]

        # Build UI
        self._build_layout()
        self._apply_styles()

        # Subscribe to engine updates (called from background thread)
        self.engine.subscribe(self._on_price_update)
        self.engine.start()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ----------------------------------------------------------
    # Layout construction
    # ----------------------------------------------------------
    def _build_layout(self):
        # ── Top navbar ──────────────────────────────────────
        self.navbar = tk.Frame(self, bg=BG_SIDEBAR, height=52)
        self.navbar.pack(fill="x", side="top")
        self.navbar.pack_propagate(False)
        self._build_navbar()

        # ── Main content (below navbar) ──────────────────────
        self.content = tk.Frame(self, bg=BG_DARK)
        self.content.pack(fill="both", expand=True)

        # Three-column layout
        self.sidebar    = tk.Frame(self.content, bg=BG_SIDEBAR, width=220)
        self.center     = tk.Frame(self.content, bg=BG_DARK)
        self.right_pane = tk.Frame(self.content, bg=BG_CARD,   width=270)

        self.sidebar.pack(side="left",  fill="y", padx=(0, 1))
        self.right_pane.pack(side="right", fill="y", padx=(1, 0))
        self.center.pack(side="left",   fill="both", expand=True)

        self.sidebar.pack_propagate(False)
        self.right_pane.pack_propagate(False)

        self._build_sidebar()
        self._build_center()
        self._build_right_panel()

    def _build_navbar(self):
        # Logo / title area
        logo_frame = tk.Frame(self.navbar, bg=BG_SIDEBAR)
        logo_frame.pack(side="left", padx=18)

        tk.Label(
            logo_frame, text="▲ MarketPulse",
            fg=ACCENT_GREEN, font=("Segoe UI", 16, "bold"),
            bg=BG_SIDEBAR
        ).pack(side="left")
        tk.Label(
            logo_frame, text=" Pro",
            fg=TEXT_PRIMARY, font=("Segoe UI", 14),
            bg=BG_SIDEBAR
        ).pack(side="left")

        # Nav tabs
        tabs_frame = tk.Frame(self.navbar, bg=BG_SIDEBAR)
        tabs_frame.pack(side="left", padx=30)

        self._active_tab = tk.StringVar(value="market")
        for label, key in [("Market", "market"), ("Portfolio", "portfolio")]:
            tk.Button(
                tabs_frame, text=label,
                command=lambda k=key: self._switch_tab(k),
                bg=BG_SIDEBAR, fg=TEXT_SECONDARY,
                font=FONT_BODY_BOLD, relief="flat", bd=0,
                cursor="hand2", padx=14, pady=12,
                activebackground=BG_SIDEBAR,
            ).pack(side="left")

        # Cash badge (top-right)
        self.cash_lbl = tk.Label(
            self.navbar,
            text="Cash: ₹1,00,000.00",
            fg=ACCENT_GREEN, font=FONT_BODY_BOLD, bg=BG_SIDEBAR
        )
        self.cash_lbl.pack(side="right", padx=20)

    def _build_sidebar(self):
        header = tk.Frame(self.sidebar, bg=BG_SIDEBAR, pady=12)
        header.pack(fill="x")
        lbl(header, "  WATCHLIST", fg=TEXT_MUTED,
            font=("Segoe UI", 9, "bold"), bg=BG_SIDEBAR).pack(anchor="w")

        sep(self.sidebar)

        # Stock rows container
        self.stock_rows: dict[str, dict] = {}
        for sym in STOCKS:
            self._add_sidebar_row(sym)

    def _add_sidebar_row(self, symbol: str):
        cfg = STOCKS[symbol]
        row = tk.Frame(self.sidebar, bg=BG_SIDEBAR, cursor="hand2")
        row.pack(fill="x", padx=8, pady=2)

        # Active indicator strip
        indicator = tk.Frame(row, bg=BG_SIDEBAR, width=3)
        indicator.pack(side="left", fill="y")

        info = tk.Frame(row, bg=BG_SIDEBAR, pady=8, padx=8)
        info.pack(side="left", fill="both", expand=True)

        sym_lbl  = lbl(info, symbol, fg=TEXT_PRIMARY, font=FONT_BODY_BOLD, bg=BG_SIDEBAR)
        name_lbl = lbl(info, cfg["name"][:20], fg=TEXT_SECONDARY, font=FONT_SMALL, bg=BG_SIDEBAR)
        sym_lbl.pack(anchor="w")
        name_lbl.pack(anchor="w")

        right_info = tk.Frame(row, bg=BG_SIDEBAR, padx=8)
        right_info.pack(side="right", pady=8)

        price_lbl  = lbl(right_info, f"₹{cfg['price']:,.2f}",
                         fg=TEXT_PRIMARY, font=FONT_BODY_BOLD, bg=BG_SIDEBAR, anchor="e")
        change_lbl = lbl(right_info, "+0.00%",
                         fg=ACCENT_GREEN, font=FONT_SMALL, bg=BG_SIDEBAR, anchor="e")
        price_lbl.pack(anchor="e")
        change_lbl.pack(anchor="e")

        # Click to select
        for widget in [row, info, right_info, sym_lbl, name_lbl, price_lbl, change_lbl]:
            widget.bind("<Button-1>", lambda e, s=symbol: self._select_stock(s))

        self.stock_rows[symbol] = {
            "row":       row,
            "indicator": indicator,
            "price":     price_lbl,
            "change":    change_lbl,
        }

        sep(self.sidebar)

    def _build_center(self):
        # Stock header
        self.chart_header = tk.Frame(self.center, bg=BG_DARK, padx=16, pady=10)
        self.chart_header.pack(fill="x")

        self.chart_sym_lbl  = lbl(self.chart_header, self._selected_symbol,
                                   fg=TEXT_PRIMARY, font=FONT_TITLE, bg=BG_DARK)
        self.chart_name_lbl = lbl(self.chart_header, "",
                                   fg=TEXT_SECONDARY, font=FONT_BODY, bg=BG_DARK)
        self.chart_price_lbl = lbl(self.chart_header, "",
                                    fg=TEXT_PRIMARY, font=FONT_PRICE, bg=BG_DARK)
        self.chart_chg_lbl  = lbl(self.chart_header, "",
                                   fg=ACCENT_GREEN, font=FONT_HEADING, bg=BG_DARK)

        self.chart_sym_lbl.pack(side="left", padx=(0, 10))
        self.chart_name_lbl.pack(side="left", pady=(6, 0))
        self.chart_chg_lbl.pack(side="right", padx=8)
        self.chart_price_lbl.pack(side="right")

        # Matplotlib figure
        self.fig, (self.ax_price, self.ax_mom) = plt.subplots(
            2, 1, figsize=(7.5, 4.8),
            facecolor=CHART_BG,
            gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05}
        )
        for ax in [self.ax_price, self.ax_mom]:
            ax.set_facecolor(CHART_BG)
            ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
            for spine in ax.spines.values():
                spine.set_edgecolor(BORDER_COLOR)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.center)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Portfolio page (hidden by default)
        self.portfolio_frame = tk.Frame(self.center, bg=BG_DARK)
        self._build_portfolio_page()

    def _build_right_panel(self):
        pane = self.right_pane

        lbl(pane, "  Order Panel", fg=TEXT_SECONDARY,
            font=("Segoe UI", 10, "bold"), bg=BG_CARD, pady=10).pack(fill="x")
        sep(pane)

        # ── Stock info summary ───────────────────────────────
        info_frame = tk.Frame(pane, bg=BG_CARD, padx=14)
        info_frame.pack(fill="x", pady=4)

        self.order_sym_lbl   = lbl(info_frame, self._selected_symbol,
                                    fg=TEXT_PRIMARY, font=FONT_HEADING, bg=BG_CARD)
        self.order_price_lbl = lbl(info_frame, "₹ ---",
                                    fg=ACCENT_GREEN, font=FONT_HEADING, bg=BG_CARD)
        self.order_sym_lbl.pack(anchor="w", pady=(4, 0))
        self.order_price_lbl.pack(anchor="w")

        sep(pane)

        # ── Quantity input ───────────────────────────────────
        qty_frame = tk.Frame(pane, bg=BG_CARD, padx=14)
        qty_frame.pack(fill="x", pady=6)

        lbl(qty_frame, "Quantity", fg=TEXT_SECONDARY, bg=BG_CARD).pack(anchor="w")

        qty_row = tk.Frame(qty_frame, bg=BG_CARD)
        qty_row.pack(fill="x", pady=4)

        tk.Button(qty_row, text="−", command=self._dec_qty,
                  bg=BG_INPUT, fg=TEXT_PRIMARY, font=FONT_HEADING,
                  relief="flat", width=3, cursor="hand2").pack(side="left")

        self.qty_var = tk.StringVar(value="1")
        self.qty_entry = tk.Entry(
            qty_row, textvariable=self.qty_var, width=7,
            bg=BG_INPUT, fg=TEXT_PRIMARY, font=FONT_BODY_BOLD,
            insertbackground=TEXT_PRIMARY, relief="flat",
            justify="center"
        )
        self.qty_entry.pack(side="left", padx=6, ipady=4)

        tk.Button(qty_row, text="+", command=self._inc_qty,
                  bg=BG_INPUT, fg=TEXT_PRIMARY, font=FONT_HEADING,
                  relief="flat", width=3, cursor="hand2").pack(side="left")

        # Order value estimate
        self.order_val_lbl = lbl(qty_frame, "Order Value: ₹ ---",
                                  fg=TEXT_SECONDARY, font=FONT_SMALL, bg=BG_CARD)
        self.order_val_lbl.pack(anchor="w", pady=2)

        sep(pane)

        # ── Buy / Sell Buttons ───────────────────────────────
        btn_frame = tk.Frame(pane, bg=BG_CARD, padx=14, pady=6)
        btn_frame.pack(fill="x")

        btn(btn_frame, "BUY",  self._do_buy,  color=ACCENT_GREEN, width=9).pack(
            side="left", padx=(0, 8))
        btn(btn_frame, "SELL", self._do_sell, color=ACCENT_RED,   fg="white", width=9).pack(
            side="left")

        # Status message
        self.order_status = lbl(pane, "", fg=ACCENT_GREEN,
                                 font=FONT_SMALL, bg=BG_CARD, wraplength=230)
        self.order_status.pack(padx=14, anchor="w")

        sep(pane)

        # ── Holdings quick-view ──────────────────────────────
        lbl(pane, "  Holdings", fg=TEXT_SECONDARY,
            font=("Segoe UI", 10, "bold"), bg=BG_CARD, pady=4).pack(fill="x")

        self.holdings_frame = tk.Frame(pane, bg=BG_CARD)
        self.holdings_frame.pack(fill="both", expand=True, padx=8, pady=4)

        # Quantity entry validation binding
        self.qty_var.trace_add("write", lambda *_: self._update_order_val())

    def _build_portfolio_page(self):
        """Build the full portfolio stats page (shown when 'Portfolio' tab clicked)."""
        page = self.portfolio_frame

        # Summary cards row
        cards_row = tk.Frame(page, bg=BG_DARK)
        cards_row.pack(fill="x", padx=12, pady=12)

        self.pf_cards: dict[str, tk.Label] = {}
        card_data = [
            ("net_worth",   "Net Worth",      "₹1,00,000.00"),
            ("cash",        "Available Cash", "₹1,00,000.00"),
            ("invested",    "Invested",       "₹0.00"),
            ("pnl",         "Total P&L",      "₹0.00 (0.00%)"),
        ]
        for key, title, init in card_data:
            card = tk.Frame(cards_row, bg=BG_CARD, bd=0, relief="flat")
            card.pack(side="left", fill="both", expand=True, padx=5, pady=5, ipadx=10, ipady=10)
            lbl(card, title, fg=TEXT_SECONDARY, font=FONT_SMALL, bg=BG_CARD).pack(anchor="w", padx=8, pady=(8,0))
            val_lbl = lbl(card, init, fg=TEXT_PRIMARY, font=FONT_HEADING, bg=BG_CARD)
            val_lbl.pack(anchor="w", padx=8, pady=(0, 8))
            self.pf_cards[key] = val_lbl

        sep(page)

        # Holdings table
        lbl(page, "  Open Positions", fg=TEXT_SECONDARY,
            font=FONT_BODY_BOLD, bg=BG_DARK, pady=6).pack(anchor="w", padx=12)

        cols_frame = tk.Frame(page, bg=BG_CARD, padx=8, pady=6)
        cols_frame.pack(fill="x", padx=12, pady=(0, 4))
        for col, w in [("Symbol", 80), ("Qty", 50), ("Avg Price", 100),
                        ("LTP", 100), ("P&L", 100), ("P&L %", 80)]:
            lbl(cols_frame, col, fg=TEXT_MUTED, font=FONT_SMALL, bg=BG_CARD, width=w//8).pack(side="left")

        self.pf_holdings_frame = tk.Frame(page, bg=BG_DARK)
        self.pf_holdings_frame.pack(fill="x", padx=12)

        sep(page)

        # Transaction history
        lbl(page, "  Transaction History", fg=TEXT_SECONDARY,
            font=FONT_BODY_BOLD, bg=BG_DARK, pady=6).pack(anchor="w", padx=12)

        # Scrollable transaction list
        hist_outer = tk.Frame(page, bg=BG_DARK)
        hist_outer.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        scrollbar = tk.Scrollbar(hist_outer, bg=BG_DARK, troughcolor=BG_CARD)
        scrollbar.pack(side="right", fill="y")

        self.tx_listbox = tk.Listbox(
            hist_outer,
            bg=BG_CARD, fg=TEXT_SECONDARY, font=("Consolas", 10),
            selectbackground=ACCENT_BLUE, activestyle="none",
            relief="flat", bd=0, yscrollcommand=scrollbar.set,
            height=8
        )
        self.tx_listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.tx_listbox.yview)

    # ----------------------------------------------------------
    # Tab switching
    # ----------------------------------------------------------
    def _switch_tab(self, tab: str):
        if tab == "market":
            self.portfolio_frame.pack_forget()
            self.chart_header.pack(fill="x")
            self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 8))
        else:
            self.chart_header.pack_forget()
            self.canvas.get_tk_widget().pack_forget()
            self.portfolio_frame.pack(fill="both", expand=True)
            self._refresh_portfolio_page()

    # ----------------------------------------------------------
    # Stock selection
    # ----------------------------------------------------------
    def _select_stock(self, symbol: str):
        self._selected_symbol = symbol
        self._update_chart_header()
        self._update_right_panel_header()
        # Highlight active row
        for sym, widgets in self.stock_rows.items():
            is_active = sym == symbol
            widgets["indicator"]["bg"] = ACCENT_BLUE if is_active else BG_SIDEBAR
            widgets["row"]["bg"] = "#1e1e28" if is_active else BG_SIDEBAR
        # Redraw chart immediately
        self._draw_chart(self.engine.stocks)

    # ----------------------------------------------------------
    # Price update callback (called from background thread)
    # ----------------------------------------------------------
    def _on_price_update(self, stocks: dict[str, StockData]):
        # Schedule UI update on main thread
        self.after(0, lambda: self._refresh_ui(stocks))

    def _refresh_ui(self, stocks: dict[str, StockData]):
        self._update_sidebar(stocks)
        self._update_chart_header()
        self._update_right_panel_header()
        self._update_order_val()
        self._draw_chart(stocks)
        self._update_holdings_quick()
        self._update_cash_badge()

    # ----------------------------------------------------------
    # Sidebar price tickers
    # ----------------------------------------------------------
    def _update_sidebar(self, stocks: dict[str, StockData]):
        for sym, sd in stocks.items():
            row = self.stock_rows.get(sym)
            if not row:
                continue
            color  = ACCENT_GREEN if sd.is_up else ACCENT_RED
            arrow  = "▲" if sd.is_up else "▼"
            pct    = sd.change_pct
            row["price"]["text"]  = f"₹{sd.price:,.2f}"
            row["change"]["text"] = f"{arrow} {abs(pct):.2f}%"
            row["change"]["fg"]   = color

    # ----------------------------------------------------------
    # Chart header labels
    # ----------------------------------------------------------
    def _update_chart_header(self):
        sd = self.engine.get(self._selected_symbol)
        cfg = STOCKS[self._selected_symbol]
        color  = ACCENT_GREEN if sd.is_up else ACCENT_RED
        arrow  = "▲" if sd.is_up else "▼"
        pct    = sd.change_pct

        self.chart_sym_lbl["text"]   = self._selected_symbol
        self.chart_name_lbl["text"]  = cfg["name"]
        self.chart_price_lbl["text"] = f"₹{sd.price:,.2f}"
        self.chart_price_lbl["fg"]   = color
        self.chart_chg_lbl["text"]   = f"{arrow} {pct:+.2f}% today"
        self.chart_chg_lbl["fg"]     = color

    # ----------------------------------------------------------
    # Right panel header
    # ----------------------------------------------------------
    def _update_right_panel_header(self):
        sd = self.engine.get(self._selected_symbol)
        color = ACCENT_GREEN if sd.is_up else ACCENT_RED
        self.order_sym_lbl["text"]   = self._selected_symbol
        self.order_price_lbl["text"] = f"₹{sd.price:,.2f}"
        self.order_price_lbl["fg"]   = color

    # ----------------------------------------------------------
    # Chart drawing (candlestick + momentum)
    # ----------------------------------------------------------
    def _draw_chart(self, stocks: dict[str, StockData]):
        sd      = stocks.get(self._selected_symbol)
        if sd is None:
            return
        candles = sd.candles
        ticks   = sd.tick_prices
        color   = sd.color

        self.ax_price.cla()
        self.ax_mom.cla()

        for ax in [self.ax_price, self.ax_mom]:
            ax.set_facecolor(CHART_BG)
            ax.tick_params(colors=TEXT_SECONDARY, labelsize=7)
            ax.grid(color=BORDER_COLOR, linewidth=0.5, alpha=0.5)
            for spine in ax.spines.values():
                spine.set_edgecolor(BORDER_COLOR)

        # ── Candlestick chart ──────────────────────────────
        if len(candles) >= 2:
            xs = list(range(len(candles)))

            for i, c in enumerate(candles):
                is_bull = c["c"] >= c["o"]
                clr     = ACCENT_GREEN if is_bull else ACCENT_RED
                # Wick (high-low line)
                self.ax_price.plot(
                    [i, i], [c["l"], c["h"]],
                    color=clr, linewidth=1, zorder=2
                )
                # Body (open-close rectangle)
                bottom = min(c["o"], c["c"])
                height = abs(c["c"] - c["o"]) or 0.01  # avoid zero-height
                rect = mpatches.Rectangle(
                    (i - 0.3, bottom), 0.6, height,
                    color=clr, linewidth=0, zorder=3
                )
                self.ax_price.add_patch(rect)

        # ── Momentum line (tick-level prices) ─────────────
        if len(ticks) > 1:
            xs_t = list(range(len(ticks)))
            self.ax_mom.plot(xs_t, ticks, color=color,
                             linewidth=1.2, alpha=0.85)
            # Shade area under line
            self.ax_mom.fill_between(xs_t, ticks,
                                     min(ticks), color=color, alpha=0.12)
            self.ax_mom.set_xlim(0, len(ticks) - 1)

        # Styling
        self.ax_price.set_ylabel("Price (₹)", color=TEXT_SECONDARY, fontsize=8)
        self.ax_mom.set_ylabel("Momentum", color=TEXT_SECONDARY, fontsize=7)
        self.ax_mom.set_xlabel("Ticks →", color=TEXT_SECONDARY, fontsize=7)

        self.fig.tight_layout(pad=0.8)
        self.canvas.draw_idle()

    # ----------------------------------------------------------
    # Holdings quick-view (right panel)
    # ----------------------------------------------------------
    def _update_holdings_quick(self):
        for w in self.holdings_frame.winfo_children():
            w.destroy()

        if not self.portfolio.holdings:
            lbl(self.holdings_frame, "No holdings",
                fg=TEXT_MUTED, font=FONT_SMALL, bg=BG_CARD).pack(anchor="w", padx=6)
            return

        for sym, holding in self.portfolio.holdings.items():
            live_price = self.engine.get(sym).price
            pnl        = self.portfolio.holding_pnl(sym, live_price) or 0
            pnl_color  = ACCENT_GREEN if pnl >= 0 else ACCENT_RED
            pnl_arrow  = "▲" if pnl >= 0 else "▼"

            row = tk.Frame(self.holdings_frame, bg=BG_CARD, pady=3)
            row.pack(fill="x", padx=4, pady=1)

            lbl(row, sym, fg=TEXT_PRIMARY, font=FONT_BODY_BOLD, bg=BG_CARD).pack(side="left")
            lbl(row, f" ×{holding.qty}", fg=TEXT_SECONDARY, font=FONT_SMALL, bg=BG_CARD).pack(side="left")
            lbl(row, f"{pnl_arrow} ₹{abs(pnl):,.0f}",
                fg=pnl_color, font=FONT_SMALL, bg=BG_CARD).pack(side="right")

    # ----------------------------------------------------------
    # Cash badge
    # ----------------------------------------------------------
    def _update_cash_badge(self):
        self.cash_lbl["text"] = f"Cash: ₹{self.portfolio.cash:,.2f}"

    # ----------------------------------------------------------
    # Quantity controls
    # ----------------------------------------------------------
    def _get_qty(self) -> int:
        try:
            return max(1, int(self.qty_var.get()))
        except ValueError:
            return 1

    def _inc_qty(self):
        self.qty_var.set(str(min(self._get_qty() + 1, MAX_TRANSACTION)))

    def _dec_qty(self):
        self.qty_var.set(str(max(1, self._get_qty() - 1)))

    def _update_order_val(self):
        try:
            qty   = int(self.qty_var.get())
            price = self.engine.get(self._selected_symbol).price
            self.order_val_lbl["text"] = f"Order Value: ₹{qty * price:,.2f}"
        except Exception:
            self.order_val_lbl["text"] = "Order Value: ₹ ---"

    # ----------------------------------------------------------
    # Buy / Sell
    # ----------------------------------------------------------
    def _do_buy(self):
        sym    = self._selected_symbol
        qty    = self._get_qty()
        price  = self.engine.get(sym).price
        name   = STOCKS[sym]["name"]
        ok, msg = self.portfolio.buy(sym, name, qty, price)
        color  = ACCENT_GREEN if ok else ACCENT_RED
        self.order_status["text"] = msg
        self.order_status["fg"]   = color
        self._update_holdings_quick()
        self._update_cash_badge()

    def _do_sell(self):
        sym   = self._selected_symbol
        qty   = self._get_qty()
        price = self.engine.get(sym).price
        ok, msg = self.portfolio.sell(sym, qty, price)
        color = ACCENT_GREEN if ok else ACCENT_RED
        self.order_status["text"] = msg
        self.order_status["fg"]   = color
        self._update_holdings_quick()
        self._update_cash_badge()

    # ----------------------------------------------------------
    # Portfolio page refresh
    # ----------------------------------------------------------
    def _refresh_portfolio_page(self):
        live_prices = {sym: self.engine.get(sym).price for sym in STOCKS}
        pf = self.portfolio

        net   = pf.net_worth(live_prices)
        inv   = pf.total_invested()
        pnl   = pf.unrealized_pnl(live_prices)
        pct   = (pnl / inv * 100) if inv > 0 else 0.0
        pnl_c = ACCENT_GREEN if pnl >= 0 else ACCENT_RED

        self.pf_cards["net_worth"]["text"] = f"₹{net:,.2f}"
        self.pf_cards["cash"]["text"]      = f"₹{pf.cash:,.2f}"
        self.pf_cards["invested"]["text"]  = f"₹{inv:,.2f}"
        self.pf_cards["pnl"]["text"]       = f"₹{pnl:+,.2f} ({pct:+.2f}%)"
        self.pf_cards["pnl"]["fg"]         = pnl_c

        # Rebuild holdings rows
        for w in self.pf_holdings_frame.winfo_children():
            w.destroy()

        if not pf.holdings:
            lbl(self.pf_holdings_frame, "  No open positions.",
                fg=TEXT_MUTED, font=FONT_SMALL, bg=BG_DARK).pack(anchor="w", pady=4)
        else:
            for sym, h in pf.holdings.items():
                lp    = live_prices[sym]
                pnl_h = pf.holding_pnl(sym, lp) or 0
                pnl_p = pf.holding_pnl_pct(sym, lp) or 0
                clr   = ACCENT_GREEN if pnl_h >= 0 else ACCENT_RED

                row = tk.Frame(self.pf_holdings_frame, bg=BG_CARD, pady=5)
                row.pack(fill="x", pady=2, padx=2)

                vals = [
                    (sym,                    TEXT_PRIMARY,   FONT_BODY_BOLD, 8),
                    (str(h.qty),             TEXT_SECONDARY, FONT_BODY,      5),
                    (f"₹{h.avg_price:,.2f}", TEXT_SECONDARY, FONT_BODY,      10),
                    (f"₹{lp:,.2f}",          TEXT_PRIMARY,   FONT_BODY,      10),
                    (f"₹{pnl_h:+,.2f}",      clr,            FONT_BODY_BOLD, 10),
                    (f"{pnl_p:+.2f}%",        clr,            FONT_BODY,      8),
                ]
                for text, fg, font, w in vals:
                    lbl(row, text, fg=fg, font=font, bg=BG_CARD, width=w).pack(side="left", padx=2)

        # Rebuild transaction history
        self.tx_listbox.delete(0, tk.END)
        for tx in reversed(pf.history[-50:]):    # show last 50, newest first
            arrow = "↑ BUY " if tx.tx_type == "BUY" else "↓ SELL"
            line  = f"  {tx.timestamp}  {arrow}  {tx.qty:>4}×{tx.symbol:<10}  @ ₹{tx.price:>10,.2f}   Total: ₹{tx.total:>12,.2f}"
            self.tx_listbox.insert(tk.END, line)
            idx = self.tx_listbox.size() - 1
            color = ACCENT_GREEN if tx.tx_type == "BUY" else ACCENT_RED
            self.tx_listbox.itemconfig(idx, fg=color)

    # ----------------------------------------------------------
    # Styles
    # ----------------------------------------------------------
    def _apply_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TScrollbar", background=BG_CARD, troughcolor=BG_DARK)
        # Select first stock
        self._select_stock(self._selected_symbol)

    # ----------------------------------------------------------
    # Cleanup
    # ----------------------------------------------------------
    def _on_close(self):
        self.engine.stop()
        plt.close("all")
        self.destroy()
