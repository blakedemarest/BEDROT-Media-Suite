import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from video_splitter.ffmpeg_splitter import build_segment_command, generate_segments, probe_video
from video_splitter.models import SplitJob


def create_sample_video(path: Path) -> None:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc=size=320x240:duration=4:rate=30",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=880:duration=4",
        "-shortest",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        str(path),
    ]
    subprocess.run(command, check=True)


class TestVideoSplitterCli(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.src = Path(self.tmpdir.name) / "fixture.mp4"
        create_sample_video(self.src)
        self.out_dir = Path(self.tmpdir.name) / "clips"
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def test_split_job_produces_clips(self):
        job = SplitJob(
            source_path=self.src,
            output_dir=self.out_dir,
            clip_length=1.5,
            jitter_percent=0.0,
            per_clip_jitter=True,
            min_clip_length=0.5,
            reset_timestamps=True,
            overwrite_existing=True,
        )

        metadata = probe_video(job.source_path)
        segments = generate_segments(job, metadata.duration, rng=random.Random(0))
        self.assertGreaterEqual(len(segments), 2)

        for segment in segments:
            command = build_segment_command(job, segment)
            subprocess.run(command, check=True)

        outputs = sorted(self.out_dir.glob("*.mp4"))
        self.assertGreaterEqual(len(outputs), len(segments))


if __name__ == "__main__":
    unittest.main()
