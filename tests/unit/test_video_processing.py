import unittest

from app.video.extractor import AudioExtractor
from app.video.frames import FrameExtractor
from app.video.metadata import extract_metadata

from app.core.exceptions import VideoProcessingError, FrameExtractionError


class TestVideoProcessing(unittest.TestCase):
    def test_metadata_missing_file(self):
        with self.assertRaises(VideoProcessingError):
            extract_metadata("nonexistent_file_12345.mp4")

    def test_audio_extractor_missing_file(self):
        ae = AudioExtractor(ffmpeg_path="ffmpeg")
        with self.assertRaises(VideoProcessingError):
            ae.extract("nonexistent_file_12345.mp4", "out.wav")

    def test_frame_extractor_missing_file(self):
        fe = FrameExtractor(sample_rate_fps=1.0, output_dir="./data/test_frames")
        with self.assertRaises(FrameExtractionError):
            fe.extract("nonexistent_file_12345.mp4", "vid123")


if __name__ == '__main__':
    unittest.main()
