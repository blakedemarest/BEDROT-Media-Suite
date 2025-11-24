import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from video_splitter.config_manager import ConfigManager


class TestVideoSplitterConfig(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.config_path = Path(self.tmpdir.name) / "config.json"

    def test_default_written(self):
        manager = ConfigManager(config_path=self.config_path)
        self.assertTrue(self.config_path.exists(), "Config file should be created")
        data = manager.get_all()
        self.assertGreater(data["clip_length_seconds"], 0)

    def test_updates_persist(self):
        manager = ConfigManager(config_path=self.config_path)
        manager.update("clip_length_seconds", 22.5)
        manager.update("jitter_percent", 12.0)

        reloaded = ConfigManager(config_path=self.config_path)
        self.assertEqual(22.5, reloaded.get("clip_length_seconds"))
        self.assertEqual(12.0, reloaded.get("jitter_percent"))


if __name__ == "__main__":
    unittest.main()
