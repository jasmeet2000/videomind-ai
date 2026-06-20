"""
VideoMind AI — Video Player Component
=======================================
Renders the video player and injects JavaScript for seeking.
"""


def get_video_player_html(video_path: str) -> str:
    """
    Returns an HTML5 video player for the given local video path.
    This is used when we want a custom-styled player rather than st.video().
    """
    return f"""
    <div class="vm-video-container">
        <video id="vm-player" controls style="width:100%; border-radius:12px;">
            <source src="{video_path}" type="video/mp4">
            Your browser does not support the video tag.
        </video>
    </div>
    """


def get_seek_script_html() -> str:
    """
    Injects the JavaScript function into the parent window (main DOM) 
    so that onclick handlers inside st.markdown can call it.
    """
    return """
    <script>
      // Define the seek function on the parent window
      window.parent.seekVideo = function(seconds) {
        try {
          // Find the video element in the parent document
          const videoElements = window.parent.document.querySelectorAll('video');
          for (let i = 0; i < videoElements.length; i++) {
            const vid = videoElements[i];
            // Only seek if it has a valid duration
            if (!isNaN(vid.duration)) {
                vid.currentTime = seconds;
                vid.play().catch(e => console.log("Auto-play blocked:", e));
                // Scroll the video into view smoothly
                vid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                return;
            }
          }
          console.warn("No video element found in parent document.");
        } catch (err) {
          console.error("Error seeking video:", err);
        }
      };
    </script>
    """
