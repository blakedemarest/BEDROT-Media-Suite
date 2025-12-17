import os
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from video_splitter.ffmpeg_splitter import generate_segments
from video_splitter.models import SplitJob


class TestVideoSplitterScheduler(unittest.TestCase):
    def _job(self, **kwargs):
        defaults = dict(
            source_path=Path("sample.mp4"),
            output_dir=Path("./out"),
            clip_length=10.0,
            jitter_percent=0.0,
            per_clip_jitter=True,
            min_clip_length=1.0,
            reset_timestamps=True,
            overwrite_existing=False,
        )
        defaults.update(kwargs)
        return SplitJob(**defaults)

    def test_generates_expected_segments_without_jitter(self):
        job = self._job()
        segments = generate_segments(job, duration=31.0, rng=random.Random(0))
        self.assertEqual(4, len(segments))
        self.assertAlmostEqual(10.0, segments[0].duration, places=2)
        self.assertAlmostEqual(1.0, segments[-1].duration, places=2)

    def test_jitter_respects_minimum(self):
        job = self._job(jitter_percent=50.0, min_clip_length=2.0)
        segments = generate_segments(job, duration=25.0, rng=random.Random(1))
        for segment in segments:
            self.assertGreaterEqual(segment.duration, 2.0)

    def test_per_file_jitter_constant(self):
        job = self._job(jitter_percent=25.0, per_clip_jitter=False)
        segments = generate_segments(job, duration=30.0, rng=random.Random(123))
        durations = {round(segment.duration, 2) for segment in segments[:-1]}
        self.assertEqual(1, len(durations), "Per-file jitter should keep clip lengths aligned")


if __name__ == "__main__":
    unittest.main()
