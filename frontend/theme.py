"""
VideoMind AI — Theme System
============================
3-mode theme switcher: Dark, Light, Glass (Glassmorphism).
Design tokens are injected as CSS custom properties.
"""

THEMES = {
    "dark": {
        "--bg-primary": "#0f1117",
        "--bg-secondary": "#1a1d27",
        "--bg-card": "#1e2130",
        "--accent": "#6c63ff",
        "--accent-hover": "#8b85ff",
        "--text-primary": "#e8eaf0",
        "--text-secondary": "#8b92a9",
        "--border": "#2e3347",
        "--success": "#00d4aa",
        "--warning": "#ffb347",
        "--error": "#ff6b6b",
        "--shimmer-base": "#1e2130",
        "--shimmer-shine": "#262a3d",
        "--radius": "12px",
        "--shadow": "0 4px 24px rgba(0,0,0,0.4)",
        "--font": "'Inter', sans-serif",
        "--font-mono": "'JetBrains Mono', monospace",
    },
    "light": {
        "--bg-primary": "#f8f9fc",
        "--bg-secondary": "#ffffff",
        "--bg-card": "#ffffff",
        "--accent": "#5b4fcf",
        "--accent-hover": "#7066e0",
        "--text-primary": "#1a1d2e",
        "--text-secondary": "#6b7280",
        "--border": "#e5e7f0",
        "--success": "#00a884",
        "--warning": "#f59e0b",
        "--error": "#ef4444",
        "--shimmer-base": "#e9ebf0",
        "--shimmer-shine": "#f5f6fa",
        "--radius": "12px",
        "--shadow": "0 2px 16px rgba(0,0,0,0.08)",
        "--font": "'Inter', sans-serif",
        "--font-mono": "'JetBrains Mono', monospace",
    },
    "glass": {
        "--bg-primary": "#0d0d1a",
        "--bg-secondary": "rgba(255,255,255,0.04)",
        "--bg-card": "rgba(255,255,255,0.06)",
        "--accent": "#a78bfa",
        "--accent-hover": "#c4b5fd",
        "--text-primary": "#f0f0ff",
        "--text-secondary": "#9ca3c8",
        "--border": "rgba(255,255,255,0.10)",
        "--success": "#34d399",
        "--warning": "#fbbf24",
        "--error": "#f87171",
        "--shimmer-base": "rgba(255,255,255,0.04)",
        "--shimmer-shine": "rgba(255,255,255,0.10)",
        "--radius": "16px",
        "--shadow": "0 8px 32px rgba(0,0,0,0.5)",
        "--font": "'Inter', sans-serif",
        "--font-mono": "'JetBrains Mono', monospace",
        "--glass-blur": "blur(16px)",
        "--glass-border": "1px solid rgba(255,255,255,0.12)",
    },
}


def get_google_fonts_html() -> str:
    """Returns the HTML to load Google Fonts."""
    return (
        '<link href="https://fonts.googleapis.com/css2?'
        "family=Inter:wght@400;500;600;700&"
        "family=JetBrains+Mono:wght@400;500&"
        'display=swap" rel="stylesheet">'
    )


def get_theme_css(theme_name: str) -> str:
    """Generate the full CSS for the given theme."""
    tokens = THEMES.get(theme_name, THEMES["dark"])
    css_vars = "\n".join(f"  {k}: {v};" for k, v in tokens.items())

    glass_card_css = ""
    if theme_name == "glass":
        glass_card_css = """
        .vm-card {
            backdrop-filter: var(--glass-blur);
            -webkit-backdrop-filter: var(--glass-blur);
            border: var(--glass-border);
        }
        """

    return f"""
    <style>
    :root {{
    {css_vars}
    }}

    /* Reset Streamlit defaults */
    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{ padding: 1.5rem 2rem; max-width: 1200px; }}

    /* Apply design tokens */
    body, .stApp {{
        background-color: var(--bg-primary) !important;
        font-family: var(--font);
        color: var(--text-primary);
    }}

    /* Streamlit sidebar */
    section[data-testid="stSidebar"] {{
        background-color: var(--bg-secondary) !important;
    }}
    section[data-testid="stSidebar"] .stMarkdown {{
        color: var(--text-primary);
    }}
    
    /* Hide sidebar toggle to keep it permanently visible */
    [data-testid="collapsedControl"] {{
        display: none !important;
    }}

    /* Streamlit tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: var(--bg-secondary);
        border-radius: var(--radius);
        padding: 4px;
        gap: 4px;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: var(--text-secondary);
        border-radius: 8px;
        font-weight: 500;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: var(--accent) !important;
        color: #fff !important;
    }}

    /* Streamlit text input */
    .stTextInput input, .stTextArea textarea {{
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
    }}

    /* Streamlit buttons */
    .stButton > button {{
        background-color: var(--accent) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: background 0.2s ease, transform 0.1s ease !important;
    }}
    .stButton > button:hover {{
        background-color: var(--accent-hover) !important;
        transform: scale(1.02);
    }}

    /* Cards */
    .vm-card {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.25rem 1.5rem;
        box-shadow: var(--shadow);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 12px;
    }}
    .vm-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(108,99,255,0.15);
    }}

    {glass_card_css}

    /* Timestamp pill */
    .vm-timestamp {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: var(--accent);
        color: #fff;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.75rem;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s ease;
        text-decoration: none;
        border: none;
    }}
    .vm-timestamp:hover {{ background: var(--accent-hover); }}

    /* Source badge */
    .vm-badge {{
        display: inline-block;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .vm-badge-speech  {{ background: rgba(0,212,170,0.15); color: var(--success); }}
    .vm-badge-ocr     {{ background: rgba(255,179,71,0.15); color: var(--warning); }}
    .vm-badge-vision  {{ background: rgba(108,99,255,0.15); color: var(--accent); }}
    .vm-badge-audio   {{ background: rgba(0,212,170,0.15); color: var(--success); }}
    .vm-badge-object  {{ background: rgba(255,179,71,0.15); color: var(--warning); }}
    .vm-badge-scene   {{ background: rgba(108,99,255,0.15); color: var(--accent); }}
    .vm-badge-visual  {{ background: rgba(255,179,71,0.15); color: var(--warning); }}

    /* Confidence bar */
    .vm-confidence-bar {{
        height: 4px;
        border-radius: 2px;
        background: linear-gradient(90deg, var(--accent), var(--success));
        transition: width 0.4s ease;
    }}

    /* Transcript snippet */
    .vm-snippet {{
        font-family: var(--font-mono);
        font-size: 0.82rem;
        color: var(--text-secondary);
        border-left: 3px solid var(--accent);
        padding-left: 0.75rem;
        margin: 0.5rem 0;
        line-height: 1.6;
    }}

    /* Chat bubbles */
    .vm-chat-user {{
        background: var(--accent);
        color: #fff;
        border-radius: 18px 18px 4px 18px;
        padding: 0.75rem 1rem;
        max-width: 75%;
        margin-left: auto;
    }}
    .vm-chat-assistant {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 18px 18px 18px 4px;
        padding: 0.75rem 1rem;
        max-width: 85%;
        color: var(--text-primary);
    }}

    /* Chat container */
    .vm-chat-container {{
        max-height: 480px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        padding: 1rem;
        scrollbar-width: thin;
        scrollbar-color: var(--border) transparent;
    }}

    /* Shimmer animation */
    @keyframes shimmer {{
        0%   {{ background-position: -600px 0; }}
        100% {{ background-position:  600px 0; }}
    }}
    .vm-skeleton {{
        background: linear-gradient(
            90deg,
            var(--shimmer-base) 25%,
            var(--shimmer-shine) 50%,
            var(--shimmer-base) 75%
        );
        background-size: 600px 100%;
        animation: shimmer 1.4s infinite ease-in-out;
        border-radius: var(--radius);
    }}
    .vm-skeleton-text  {{ height: 14px; margin-bottom: 8px; border-radius: 4px; }}
    .vm-skeleton-title {{ height: 20px; width: 60%; margin-bottom: 12px; border-radius: 4px; }}
    .vm-skeleton-badge {{ height: 20px; width: 80px; border-radius: 20px; }}
    .vm-skeleton-bar   {{ height: 4px;  border-radius: 2px; }}
    .vm-skeleton-video {{ height: 200px; border-radius: var(--radius); }}

    /* Upload zone animation */
    @keyframes dash-pulse {{
        0%, 100% {{ border-color: var(--accent); opacity: 0.6; }}
        50%      {{ border-color: var(--accent-hover); opacity: 1; }}
    }}
    .vm-upload-zone {{
        border: 2px dashed var(--accent);
        border-radius: var(--radius);
        padding: 2rem;
        text-align: center;
        animation: dash-pulse 2s infinite ease-in-out;
    }}

    /* Video player glow */
    .vm-video-container {{
        border-radius: var(--radius);
        overflow: hidden;
        box-shadow: 0 0 20px rgba(108,99,255,0.3);
        border: 2px solid var(--accent);
    }}
    .vm-video-container video {{
        width: 100%;
        display: block;
    }}

    /* Theme toggle buttons */
    .vm-theme-btn {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        border: 1px solid var(--border);
        background: var(--bg-card);
        cursor: pointer;
        font-size: 1.1rem;
        transition: all 0.2s ease;
    }}
    .vm-theme-btn:hover {{
        border-color: var(--accent);
        box-shadow: 0 0 8px rgba(108,99,255,0.3);
    }}
    .vm-theme-btn.active {{
        border-color: var(--accent);
        background: var(--accent);
        box-shadow: 0 0 12px rgba(108,99,255,0.5);
    }}

    /* Pipeline stepper */
    .vm-stepper {{
        display: flex;
        flex-direction: column;
        gap: 0;
    }}
    .vm-step {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 6px 0;
        font-size: 0.85rem;
        color: var(--text-secondary);
    }}
    .vm-step.active {{
        color: var(--accent);
        font-weight: 600;
    }}
    .vm-step.done {{
        color: var(--success);
    }}
    .vm-step-icon {{
        width: 22px;
        height: 22px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        font-size: 0.7rem;
        border: 2px solid var(--border);
    }}
    .vm-step.done .vm-step-icon {{
        border-color: var(--success);
        background: rgba(0,212,170,0.15);
    }}
    .vm-step.active .vm-step-icon {{
        border-color: var(--accent);
        background: rgba(108,99,255,0.15);
    }}
    .vm-step-line {{
        width: 2px;
        height: 12px;
        background: var(--border);
        margin-left: 10px;
    }}

    /* Empty states */
    .vm-empty-state {{
        text-align: center;
        padding: 3rem 1rem;
        color: var(--text-secondary);
    }}
    .vm-empty-state .icon {{
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }}
    .vm-empty-state p {{
        font-size: 0.95rem;
        margin: 0;
    }}

    /* Expander styling */
    .streamlit-expanderHeader {{
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border-radius: var(--radius) !important;
    }}

    </style>
    """
