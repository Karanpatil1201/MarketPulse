# ============================================================
# config.py — App-wide constants and stock configuration
# ============================================================

# ---------- Window / Layout ----------
APP_TITLE       = "MarketPulse — Indian Market Dashboard"
WINDOW_WIDTH    = 1300
WINDOW_HEIGHT   = 780
UPDATE_INTERVAL = 1200   # milliseconds between price ticks

# ---------- Color Palette (Groww-inspired dark theme) ----------
BG_DARK        = "#0f0f11"   # main window background
BG_CARD        = "#1a1a1f"   # card / panel background
BG_SIDEBAR     = "#13131a"   # left sidebar
BG_INPUT       = "#23232d"   # text-entry fields
ACCENT_GREEN   = "#00d09c"   # profit / buy
ACCENT_RED     = "#f0616d"   # loss / sell
ACCENT_BLUE    = "#4d8af0"   # highlight / active
TEXT_PRIMARY   = "#f4f4f5"   # main text
TEXT_SECONDARY = "#8b8b9e"   # muted labels
TEXT_MUTED     = "#4e4e60"   # disabled / placeholder
BORDER_COLOR   = "#2a2a38"   # subtle borders
CHART_BG       = "#0f0f11"   # matplotlib chart background

# ---------- Font Definitions ----------
FONT_TITLE     = ("Segoe UI", 18, "bold")
FONT_HEADING   = ("Segoe UI", 12, "bold")
FONT_BODY      = ("Segoe UI", 10)
FONT_BODY_BOLD = ("Segoe UI", 10, "bold")
FONT_SMALL     = ("Segoe UI", 9)
FONT_MONO      = ("Consolas", 10)
FONT_PRICE     = ("Segoe UI", 22, "bold")

# ---------- Simulated Stock Universe ----------
# Each entry: symbol → { display name, starting price, drift, volatility }
STOCKS = {
    "RELIANCE": {
        "name":       "Reliance Industries",
        "price":      2850.00,
        "drift":      0.0002,    # slight upward bias per tick
        "volatility": 0.0035,   # std-dev of random shock
        "color":      "#4d8af0",
    },
    "TCS": {
        "name":       "Tata Consultancy Services",
        "price":      3740.00,
        "drift":      0.00015,
        "volatility": 0.003,
        "color":      "#a78bfa",
    },
    "INFY": {
        "name":       "Infosys Ltd",
        "price":      1580.00,
        "drift":      0.00018,
        "volatility": 0.0032,
        "color":      "#38bdf8",
    },
    "HDFCBANK": {
        "name":       "HDFC Bank Ltd",
        "price":      1640.00,
        "drift":      0.00012,
        "volatility": 0.0028,
        "color":      "#fb923c",
    },
    "WIPRO": {
        "name":       "Wipro Ltd",
        "price":      462.00,
        "drift":      0.00010,
        "volatility": 0.004,
        "color":      "#34d399",
    },
}

# ---------- Simulation ----------
PRICE_HISTORY_LEN = 80      # candles to store per stock
CANDLE_PERIOD     = 5       # ticks per candle (OHLC aggregation)

# ---------- Portfolio ----------
STARTING_CASH     = 100_000.0   # ₹1 lakh demo cash
MAX_TRANSACTION   = 500         # max quantity per order
