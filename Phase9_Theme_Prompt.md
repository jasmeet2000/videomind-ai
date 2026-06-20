# Phase 9 — UI/UX Theme Specification 

## Theme System

Build a **3-mode theme switcher** stored in `st.session_state["theme"]`:
- `"dark"` — Professional dev tool aesthetic
- `"light"` — Clean, airy, editorial
- `"glass"` — Glassmorphism (the showstopper for recruiters)

Inject all theme CSS globally via `st.markdown("<style>...</style>", unsafe_allow_html=True)` 
on every rerun, reading from `st.session_state["theme"]`.

Place the theme toggle in the top-right of the sidebar as three small icon buttons 
(🌙 / ☀️ / 🪟), not a dropdown — icon buttons feel more modern.

---

## Design Tokens (define these as Python dicts, one per theme)

```python
THEMES = {
    "dark": {
        "--bg-primary":     "#0f1117",
        "--bg-secondary":   "#1a1d27",
        "--bg-card":        "#1e2130",
        "--accent":         "#6c63ff",   # purple — premium feel
        "--accent-hover":   "#8b85ff",
        "--text-primary":   "#e8eaf0",
        "--text-secondary": "#8b92a9",
        "--border":         "#2e3347",
        "--success":        "#00d4aa",
        "--warning":        "#ffb347",
        "--error":          "#ff6b6b",
        "--shimmer-base":   "#1e2130",
        "--shimmer-shine":  "#262a3d",
        "--radius":         "12px",
        "--shadow":         "0 4px 24px rgba(0,0,0,0.4)",
        "--font":           "'Inter', sans-serif",
        "--font-mono":      "'JetBrains Mono', monospace",
    },
    "light": {
        "--bg-primary":     "#f8f9fc",
        "--bg-secondary":   "#ffffff",
        "--bg-card":        "#ffffff",
        "--accent":         "#5b4fcf",
        "--accent-hover":   "#7066e0",
        "--text-primary":   "#1a1d2e",
        "--text-secondary": "#6b7280",
        "--border":         "#e5e7f0",
        "--success":        "#00a884",
        "--warning":        "#f59e0b",
        "--error":          "#ef4444",
        "--shimmer-base":   "#e9ebf0",
        "--shimmer-shine":  "#f5f6fa",
        "--radius":         "12px",
        "--shadow":         "0 2px 16px rgba(0,0,0,0.08)",
        "--font":           "'Inter', sans-serif",
        "--font-mono":      "'JetBrains Mono', monospace",
    },
    "glass": {
        "--bg-primary":     "#0d0d1a",
        "--bg-secondary":   "rgba(255,255,255,0.04)",
        "--bg-card":        "rgba(255,255,255,0.06)",
        "--accent":         "#a78bfa",
        "--accent-hover":   "#c4b5fd",
        "--text-primary":   "#f0f0ff",
        "--text-secondary": "#9ca3c8",
        "--border":         "rgba(255,255,255,0.10)",
        "--success":        "#34d399",
        "--warning":        "#fbbf24",
        "--error":          "#f87171",
        "--shimmer-base":   "rgba(255,255,255,0.04)",
        "--shimmer-shine":  "rgba(255,255,255,0.10)",
        "--radius":         "16px",
        "--shadow":         "0 8px 32px rgba(0,0,0,0.5)",
        "--font":           "'Inter', sans-serif",
        "--font-mono":      "'JetBrains Mono', monospace",
        "--glass-blur":     "blur(16px)",
        "--glass-border":   "1px solid rgba(255,255,255,0.12)",
    }
}
```

Import Inter and JetBrains Mono from Google Fonts via a single `st.markdown()` call on app load:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

---

## Global CSS Rules (applied to all themes)

```css
/* Reset Streamlit defaults */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem; max-width: 1200px; }

/* Apply design tokens */
body, .stApp {
  background-color: var(--bg-primary);
  font-family: var(--font);
  color: var(--text-primary);
}

/* Cards */
.vm-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.25rem 1.5rem;
  box-shadow: var(--shadow);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.vm-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(108,99,255,0.15);
}

/* Glass card override */
.vm-card-glass {
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: var(--glass-border);
}

/* Accent button */
.vm-btn {
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1.25rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.1s ease;
}
.vm-btn:hover {
  background: var(--accent-hover);
  transform: scale(1.02);
}

/* Timestamp pill */
.vm-timestamp {
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
}
.vm-timestamp:hover { background: var(--accent-hover); }

/* Source badge */
.vm-badge {
  display: inline-block;
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.vm-badge-speech  { background: rgba(0,212,170,0.15); color: var(--success); }
.vm-badge-ocr     { background: rgba(255,179,71,0.15);  color: var(--warning); }
.vm-badge-vision  { background: rgba(108,99,255,0.15);  color: var(--accent);  }

/* Confidence bar */
.vm-confidence-bar {
  height: 4px;
  border-radius: 2px;
  background: linear-gradient(90deg, var(--accent), var(--success));
  transition: width 0.4s ease;
}

/* Transcript snippet */
.vm-snippet {
  font-family: var(--font-mono);
  font-size: 0.82rem;
  color: var(--text-secondary);
  border-left: 3px solid var(--accent);
  padding-left: 0.75rem;
  margin: 0.5rem 0;
  line-height: 1.6;
}

/* Chat bubbles */
.vm-chat-user {
  background: var(--accent);
  color: #fff;
  border-radius: 18px 18px 4px 18px;
  padding: 0.75rem 1rem;
  max-width: 75%;
  margin-left: auto;
}
.vm-chat-assistant {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 18px 18px 18px 4px;
  padding: 0.75rem 1rem;
  max-width: 85%;
}

/* Scrollable chat container */
.vm-chat-container {
  max-height: 480px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}
```

---

## Skeleton / Shimmer Loaders

Use skeleton loaders in **every place where data is being fetched** — never show a raw 
`st.spinner()` alone. Combine `st.empty()` + `st.components.v1.html()` to inject shimmer HTML,
then replace with real content once the API responds.

### Shimmer CSS (injected once globally)

```css
@keyframes shimmer {
  0%   { background-position: -600px 0; }
  100% { background-position:  600px 0; }
}

.vm-skeleton {
  background: linear-gradient(
    90deg,
    var(--shimmer-base) 25%,
    var(--shimmer-shine) 50%,
    var(--shimmer-base) 75%
  );
  background-size: 600px 100%;
  animation: shimmer 1.4s infinite ease-in-out;
  border-radius: var(--radius);
}

.vm-skeleton-text  { height: 14px; margin-bottom: 8px; border-radius: 4px; }
.vm-skeleton-title { height: 20px; width: 60%; margin-bottom: 12px; border-radius: 4px; }
.vm-skeleton-badge { height: 20px; width: 80px; border-radius: 20px; }
.vm-skeleton-bar   { height: 4px;  border-radius: 2px; }
.vm-skeleton-video { height: 200px; border-radius: var(--radius); }
.vm-skeleton-thumb { height: 48px; width: 48px; border-radius: 50%; }
```

### Where to show skeletons

| Trigger | Skeleton shown |
|---|---|
| Video uploading | Full skeleton card with shimmer video block + 3 text lines |
| Processing status polling | Skeleton status bar replacing the real progress bar |
| Chat waiting for LLM response | 3 lines of shimmer text in an assistant bubble |
| Search results loading | 3 skeleton result cards stacked |
| Video metadata loading | Shimmer title + 2 shimmer text lines |

### Implementation pattern

```python
def show_skeleton_results():
    return """
    <div style="display:flex;flex-direction:column;gap:12px;">
      """ + "".join([f"""
      <div class="vm-card vm-skeleton-card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <div class="vm-skeleton vm-skeleton-badge"></div>
          <div class="vm-skeleton vm-skeleton-badge" style="width:60px;"></div>
        </div>
        <div class="vm-skeleton vm-skeleton-title"></div>
        <div class="vm-skeleton vm-skeleton-text" style="width:100%"></div>
        <div class="vm-skeleton vm-skeleton-text" style="width:85%"></div>
        <div class="vm-skeleton vm-skeleton-text" style="width:70%"></div>
        <div class="vm-skeleton vm-skeleton-bar" style="width:100%;margin-top:10px;"></div>
      </div>
      """ for _ in range(3)]) + """
    </div>
    """

# Usage
placeholder = st.empty()
placeholder.markdown(show_skeleton_results(), unsafe_allow_html=True)
results = requests.post("/api/v1/search", json=payload, timeout=30).json()
placeholder.empty()
# render real results
```

---

## Additional Modern UI Components

### 1. Animated Status Pipeline Tracker
In the sidebar, show the processing pipeline as a visual stepper — not just text:
```
[✓] Audio Extracted
[✓] Transcribed  
[⟳] OCR Running...   ← animated spinner on active step
[ ] Embeddings
[ ] Ready
```
Each step is a small row with an icon, label, and subtle connector line between steps.
Poll `/api/v1/videos/{video_id}` every 3 seconds using `st.empty()` + `time.sleep(3)`.

### 2. Floating Video Player
Render the video in a styled container with rounded corners, a subtle glow border using 
`--accent` color, and a timestamp display overlay. Use `st.video()` as the base, wrapped 
in a custom `<div>` for styling.

### 3. Search Result Cards
Each result is a `vm-card` containing:
- Top row: source badge (SPEECH / OCR / VISION) + confidence score + clickable timestamp pill
- Middle: transcript/OCR snippet in monospace with keyword highlighting
- Bottom: thin confidence bar (width = score × 100%)
- Hover: card lifts 2px with accent-colored shadow

### 4. Chat Interface
- User messages: right-aligned purple bubble
- Assistant messages: left-aligned card with cited sources shown as inline timestamp pills below the answer text
- Input: a fixed-bottom text input that doesn't push content up on mobile
- Empty state: centered illustration placeholder with text "Ask anything about your video"

### 5. Micro-interactions
- All cards have `transition: transform 0.2s ease` hover lift
- Buttons scale to `1.02` on hover
- Timestamp pills brighten on hover
- Theme switcher icons have a subtle glow when active
- Upload area pulses with a dashed animated border when dragging a file over it:
```css
@keyframes dash-pulse {
  0%, 100% { border-color: var(--accent); opacity: 0.6; }
  50%       { border-color: var(--accent-hover); opacity: 1; }
}
.vm-upload-zone {
  border: 2px dashed var(--accent);
  border-radius: var(--radius);
  padding: 2rem;
  text-align: center;
  animation: dash-pulse 2s infinite ease-in-out;
}
```

### 6. Toast Notifications
Use `st.toast()` for non-blocking feedback:
- ✅ "Video uploaded successfully" (success — green)
- ⚙️ "Processing started..." (info — accent)  
- ❌ "Upload failed — check file format" (error — red)
Never use `st.error()` / `st.success()` for transient messages — they break layout flow.

### 7. Empty States
Every tab needs a designed empty state, not a blank screen:
- **Chat tab (no video):** Icon + "Upload a video to start chatting"
- **Search tab (no results):** Icon + "No results found — try different keywords"
- **Processing:** Animated skeleton cards + "Analyzing your video..."

---

## Layout Structure

```
┌─ Sidebar (280px) ───────────────┐  ┌─ Main Area ─────────────────────────────┐
│  [Logo] VideoMind AI    🌙☀️🪟  │  │  ┌─ Video Player ──────────────────────┐ │
│  ─────────────────────────────  │  │  │  [video with accent glow border]    │ │
│  📁 Upload Video                │  │  │  Duration: 00:00 / 45:32            │ │
│  [drag & drop zone]             │  │  └─────────────────────────────────────┘ │
│  ─────────────────────────────  │  │                                          │
│  ⚙️ Processing Status           │  │  [💬 Chat]  [🔍 Search]  [📋 Summary]   │
│  [animated stepper]             │  │  ──────────────────────────────────────  │
│  ─────────────────────────────  │  │  (Tab content — chat / search / summary) │
│  📂 Recent Videos               │  │                                          │
│  [list of past videos]          │  └──────────────────────────────────────────┘
└─────────────────────────────────┘
```

---

## File Checklist for Phase 9

- `frontend/app.py` — main Streamlit app
- `frontend/theme.py` — `THEMES` dict + `inject_theme(theme_name)` function
- `frontend/components/skeleton.py` — all skeleton HTML generators
- `frontend/components/cards.py` — result card, chat bubble renderers
- `frontend/components/player.py` — video player with JS seek integration
- `frontend/components/status.py` — animated pipeline stepper
- `frontend/requirements.txt` — streamlit, requests, (no other deps needed)

---

## Approval Checklist Before Phase 10

Manually verify all of the following:

- [ ] Theme switcher toggles all 3 modes with instant CSS change, no page flash
- [ ] Skeleton loaders appear during upload, processing poll, chat wait, and search
- [ ] Video player renders with accent glow border
- [ ] Timestamp pills in search/chat results seek the video player on click
- [ ] Pipeline stepper updates live every 3 seconds during processing
- [ ] Chat history persists in session state across messages
- [ ] Search cards show badge, confidence bar, snippet, and timestamp
- [ ] Toast notifications fire on upload success, error, and processing start
- [ ] All empty states are designed (no blank screens)
- [ ] All API errors show user-friendly messages (no raw Python tracebacks)
- [ ] CORS allows `http://localhost:8501` in `app/main.py`
