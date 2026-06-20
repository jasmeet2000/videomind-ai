import unittest
from unittest.mock import MagicMock, patch

from app.video.extractor import AudioExtractor
from app.video.frames import FrameExtractor
from app.video.processor import VideoProcessor


class TestVideoProcessorOrchestrator(unittest.TestCase):
    def test_process_calls_subcomponents_and_returns_summary(self):
        video_path = "some/path.mp4"
        video_id = "vid123"
        audio_path = "out.wav"
        fake_frame = MagicMock()
        fake_frame.file_path = "frame1.jpg"
        fake_frame.timestamp_seconds = 1.0
        frames = [fake_frame]
        metadata = {
            "duration_seconds": 10.0,
            "fps": 30.0,
            "width": 640,
            "height": 480,
            "codec": "h264",
        }

        with (
            patch(
                "app.video.extractor.AudioExtractor.extract", return_value=audio_path
            ) as mock_audio,
            patch("app.video.frames.FrameExtractor.extract", return_value=frames) as mock_frames,
            patch("app.video.processor.extract_metadata", return_value=metadata) as mock_meta,
        ):
            proc = VideoProcessor(
                audio_extractor=AudioExtractor(),
                frame_extractor=FrameExtractor(),
                output_dir="./data/tmp",
            )
            summary = proc.process(video_path, video_id)

            mock_meta.assert_called_once_with(video_path)
            mock_audio.assert_called_once()
            mock_frames.assert_called_once()

            self.assertEqual(summary["metadata"], metadata)
            self.assertEqual(summary["audio_path"], audio_path)
            self.assertEqual(summary["frames"], frames)


if __name__ == "__main__":
    unittest.main()
