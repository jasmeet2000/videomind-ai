"""
VideoMind AI — Skeleton / Shimmer Loaders
==========================================
HTML generators for skeleton loading states.
"""


def skeleton_results(count: int = 3) -> str:
    """Generate skeleton cards for search results loading."""
    cards = ""
    for _ in range(count):
        cards += """
        <div class="vm-card" style="margin-bottom:12px;">
          <div style="display:flex;justify-content:space-between;
                      align-items:center;margin-bottom:8px;">
            <div class="vm-skeleton vm-skeleton-badge"></div>
            <div class="vm-skeleton vm-skeleton-badge"
                 style="width:60px;"></div>
          </div>
          <div class="vm-skeleton vm-skeleton-title"></div>
          <div class="vm-skeleton vm-skeleton-text"
               style="width:100%"></div>
          <div class="vm-skeleton vm-skeleton-text"
               style="width:85%"></div>
          <div class="vm-skeleton vm-skeleton-text"
               style="width:70%"></div>
          <div class="vm-skeleton vm-skeleton-bar"
               style="width:100%;margin-top:10px;"></div>
        </div>
        """
    return f'<div style="display:flex;flex-direction:column;gap:12px;">{cards}</div>'


def skeleton_chat_response() -> str:
    """Generate skeleton for an assistant chat bubble loading."""
    return """
    <div class="vm-chat-assistant" style="margin-bottom:12px;">
      <div class="vm-skeleton vm-skeleton-text" style="width:90%"></div>
      <div class="vm-skeleton vm-skeleton-text" style="width:75%"></div>
      <div class="vm-skeleton vm-skeleton-text" style="width:60%"></div>
    </div>
    """


def skeleton_video() -> str:
    """Generate skeleton for video player area."""
    return """
    <div class="vm-card" style="margin-bottom:12px;">
      <div class="vm-skeleton vm-skeleton-video"></div>
      <div class="vm-skeleton vm-skeleton-title"
           style="margin-top:12px;"></div>
      <div class="vm-skeleton vm-skeleton-text"
           style="width:80%;"></div>
    </div>
    """


def skeleton_status() -> str:
    """Generate skeleton for the processing status stepper."""
    steps = ""
    for _ in range(5):
        steps += """
        <div style="display:flex;align-items:center;gap:10px;
                    padding:6px 0;">
          <div class="vm-skeleton" style="width:22px;height:22px;
               border-radius:50%;"></div>
          <div class="vm-skeleton vm-skeleton-text"
               style="width:120px;margin:0;"></div>
        </div>
        """
    return steps
