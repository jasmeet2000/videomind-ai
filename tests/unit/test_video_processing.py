import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from app.core.exceptions import FrameExtractionError, VideoProcessingError
from app.video.extractor import AudioExtractor
from app.video.frames import FrameExtractor
from app.video.metadata import extract_metadata


class TestVideoProcessing(unittest.TestCase):
    def test_metadata_missing_file(self):
        with self.assertRaises(VideoProcessingError):
            extract_metadata("nonexistent_file_12345.mp4")

    @patch("shutil.which", return_value="/usr/bin/ffprobe")
    @patch("subprocess.run")
    def test_metadata_ffprobe_success(self, mock_run, mock_which):
        mock_stdout = """{
            "format": {
                "duration": "10.5"
            },
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 640,
                    "height": 480,
                    "avg_frame_rate": "30/1"
                }
            ]
        }"""
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_stdout, stderr="")
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_name = tmp.name
        try:
            res = extract_metadata(tmp_name)
            self.assertEqual(res["duration_seconds"], 10.5)
            self.assertEqual(res["fps"], 30.0)
            self.assertEqual(res["width"], 640)
            self.assertEqual(res["height"], 480)
            self.assertEqual(res["codec"], "h264")
        finally:
            os.unlink(tmp_name)

    @patch("shutil.which", return_value="/usr/bin/ffprobe")
    @patch("subprocess.run")
    def test_metadata_ffprobe_failure(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="some error")
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_name = tmp.name
        try:
            with self.assertRaises(VideoProcessingError):
                extract_metadata(tmp_name)
        finally:
            os.unlink(tmp_name)

    @patch("shutil.which", return_value="/usr/bin/ffprobe")
    @patch("subprocess.run")
    def test_metadata_ffprobe_parse_error(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(returncode=0, stdout="invalid json", stderr="")
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_name = tmp.name
        try:
            with self.assertRaises(VideoProcessingError):
                extract_metadata(tmp_name)
        finally:
            os.unlink(tmp_name)

    @patch("shutil.which", return_value=None)
    @patch("sys.modules", {"cv2": MagicMock()})
    def test_metadata_opencv_fallback(self, mock_which):
        import cv2

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 25.0,
            cv2.CAP_PROP_FRAME_COUNT: 250,
            cv2.CAP_PROP_FRAME_WIDTH: 1280,
            cv2.CAP_PROP_FRAME_HEIGHT: 720,
        }.get(prop, 0.0)
        cv2.VideoCapture.return_value = mock_cap

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_name = tmp.name
        try:
            res = extract_metadata(tmp_name)
            self.assertEqual(res["duration_seconds"], 10.0)
            self.assertEqual(res["fps"], 25.0)
            self.assertEqual(res["width"], 1280)
            self.assertEqual(res["height"], 720)
            self.assertEqual(res["codec"], "")
        finally:
            os.unlink(tmp_name)

    def test_audio_extractor_missing_file(self):
        ae = AudioExtractor(ffmpeg_path="ffmpeg")
        with self.assertRaises(VideoProcessingError):
            ae.extract("nonexistent_file_12345.mp4", "out.wav")

    @patch("shutil.which", return_value="/usr/bin/ffmpeg")
    @patch("subprocess.run")
    def test_audio_extractor_success(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        ae = AudioExtractor(ffmpeg_path="ffmpeg")
        with (
            tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_in,
            tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_out,
        ):
            tmp_in_name = tmp_in.name
            tmp_out_name = tmp_out.name
        try:
            res = ae.extract(tmp_in_name, tmp_out_name)
            self.assertTrue(os.path.isabs(res))
        finally:
            os.unlink(tmp_in_name)
            os.unlink(tmp_out_name)

    def test_frame_extractor_missing_file(self):
        fe = FrameExtractor(sample_rate_fps=1.0, output_dir="./data/test_frames")
        with self.assertRaises(FrameExtractionError):
            fe.extract("nonexistent_file_12345.mp4", "vid123")

    @patch("sys.modules", {"cv2": MagicMock()})
    def test_frame_extractor_success(self):
        import cv2

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 10.0,
            cv2.CAP_PROP_FRAME_COUNT: 100,
        }.get(prop, 0.0)
        mock_cap.read.side_effect = [(True, MagicMock()), (True, MagicMock()), (False, None)]
        cv2.VideoCapture.return_value = mock_cap
        cv2.IMWRITE_JPEG_QUALITY = 1
        cv2.imwrite.return_value = True

        fe = FrameExtractor(sample_rate_fps=1.0, output_dir="./data/test_frames")
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_name = tmp.name
        try:
            frames = fe.extract(tmp_name, "vid123")
            self.assertTrue(len(frames) > 0)
            self.assertEqual(frames[0].video_id, "vid123")
        finally:
            os.unlink(tmp_name)


if __name__ == "__main__":
    unittest.main()
