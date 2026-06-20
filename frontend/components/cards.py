"""
VideoMind AI — Card Components
===============================
Renderers for search results and chat bubbles.
"""

from typing import Dict, Any


def get_badge_class(modality: str) -> str:
    """Return the CSS class for a modality badge."""
    mod = str(modality).lower()
    if mod in ("speech", "audio"):
        return "vm-badge-speech"
    elif mod in ("ocr", "text"):
        return "vm-badge-ocr"
    elif mod in ("vision", "visual", "object", "scene"):
        return "vm-badge-vision"
    return "vm-badge-speech"


def render_search_result(result: Dict[str, Any]) -> str:
    """Generate HTML for a single search result card."""
    modality = result.get("modality", "speech")
    badge_class = get_badge_class(modality)
    score = result.get("score", 0.0)
    score_pct = min(100, max(0, int(score * 100)))
    text = result.get("text", "")
    timestamp_label = result.get("timestamp_label", "00:00")
    start_seconds = result.get("start_seconds", 0)

    # Note: onclick calls our injected JS function seekVideo()
    return f"""
    <div class="vm-card" style="margin-bottom:12px;">
      <div style="display:flex;justify-content:space-between;
                  align-items:center;margin-bottom:8px;">
        <div>
            <span class="vm-badge {badge_class}">{modality.upper()}</span>
            <span style="font-size:0.75rem;color:var(--text-secondary);
                         margin-left:8px;font-weight:600;">
                {score_pct}% Match
            </span>
        </div>
        <button class="vm-timestamp" onclick="window.parent.seekVideo({start_seconds})"
                title="Seek to {timestamp_label}">
            ▶ {timestamp_label}
        </button>
      </div>
      <div class="vm-snippet">
        {text}
      </div>
      <div style="background:var(--shimmer-base);height:4px;
                  border-radius:2px;margin-top:10px;overflow:hidden;">
        <div class="vm-confidence-bar" style="width:{score_pct}%;"></div>
      </div>
    </div>
    """


def render_chat_user(text: str) -> str:
    """Generate HTML for a user chat bubble."""
    return f"""
    <div style="display:flex;width:100%;margin-bottom:12px;">
      <div class="vm-chat-user">
        {text}
      </div>
    </div>
    """


def render_chat_assistant(text: str, sources: list[Dict[str, Any]] = None) -> str:
    """Generate HTML for an assistant chat bubble with source citations."""
    sources_html = ""
    if sources:
        sources_html += '<div style="margin-top:12px;display:flex;gap:6px;flex-wrap:wrap;">'
        # Deduplicate sources based on chunk_id or timestamp
        seen = set()
        for s in sources:
            start_sec = s.get("start_seconds", 0)
            if start_sec in seen:
                continue
            seen.add(start_sec)
            
            label = s.get("timestamp_label", "00:00")
            # Note: onclick calls our injected JS function seekVideo()
            sources_html += f"""
            <button class="vm-timestamp" onclick="window.parent.seekVideo({start_sec})"
                    title="Source: {s.get('modality', 'Unknown')}">
                ▶ {label}
            </button>
            """
        sources_html += '</div>'

    # Convert simple newlines to HTML br for chat display
    formatted_text = text.replace("\n", "<br>")

    return f"""
    <div style="display:flex;width:100%;margin-bottom:12px;">
      <div class="vm-chat-assistant">
        <div>{formatted_text}</div>
        {sources_html}
      </div>
    </div>
    """
