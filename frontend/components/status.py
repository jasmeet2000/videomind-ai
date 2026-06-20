"""
VideoMind AI — Status Component
================================
Renders the animated processing status pipeline.
"""

def render_pipeline_stepper(status_text: str) -> str:
    """
    Generate the HTML for an animated processing pipeline stepper.
    status_text is the `progress_message` returned from the API.
    """
    
    # Simple heuristic to determine which step is active based on progress message
    status_lower = status_text.lower()
    
    steps = [
        {"id": "audio", "label": "Extracting Audio"},
        {"id": "transcribe", "label": "Transcribing Speech"},
        {"id": "ocr", "label": "Extracting OCR & Vision"},
        {"id": "embed", "label": "Generating Embeddings"},
        {"id": "done", "label": "Ready"}
    ]
    
    # Determine current step index
    current_idx = 0
    if "complete" in status_lower or "success" in status_lower:
        current_idx = 4
    elif "embed" in status_lower or "index" in status_lower:
        current_idx = 3
    elif "ocr" in status_lower or "vision" in status_lower or "scene" in status_lower:
        current_idx = 2
    elif "transcrib" in status_lower or "whisper" in status_lower:
        current_idx = 1
    
    html = '<div class="vm-stepper">'
    
    for i, step in enumerate(steps):
        is_done = i < current_idx
        is_active = i == current_idx and current_idx < 4
        
        # Determine icon
        if is_done or (i == 4 and current_idx == 4):
            icon = "✓"
            state_class = "done"
        elif is_active:
            icon = "⟳"
            state_class = "active"
        else:
            icon = ""
            state_class = ""
            
        # Add spinning animation inline if active
        icon_html = f'<div class="vm-step-icon" {"style=\'animation: spin 2s linear infinite;\'" if is_active else ""}>{icon}</div>'
        
        html += f"""
        <div class="vm-step {state_class}">
            {icon_html}
            <div>{step['label']}</div>
        </div>
        """
        
        # Add connector line except for last item
        if i < len(steps) - 1:
            html += '<div class="vm-step-line"></div>'
            
    html += '</div>'
    
    # Add keyframes if active
    if current_idx < 4:
        html += """
        <style>
            @keyframes spin { 100% { transform: rotate(360deg); } }
        </style>
        """
        
    return html
