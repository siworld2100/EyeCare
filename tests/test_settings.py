"""Settings / ConfigManager 单元测试：边界裁剪、缺字段容错、损坏文件降级、原子写入"""

import json
import os
import tempfile
import unittest

from eye_care.config.manager import ConfigManager
from eye_care.config.settings import Settings


class SettingsTest(unittest.TestCase):
    def test_defaults(self):
        settings = Settings()
        self.assertEqual(settings.rest_interval, 20)
        self.assertFalse(settings.paused)

    def test_missing_fields_fall_back_to_defaults(self):
        # 旧版本配置文件没有 paused 字段（真实存在的场景）
        settings = Settings.from_dict({"rest_interval": 30, "rest_opacity": 50})
        self.assertEqual(settings.rest_interval, 30)
        self.assertEqual(settings.rest_opacity, 50)
        self.assertFalse(settings.paused)
        self.assertTrue(settings.autostart)

    def test_out_of_range_values_are_clamped_or_ignored(self):
        settings = Settings.from_dict(
            {"rest_interval": 0, "rest_opacity": 300, "blink_duration": 0.1}
        )
        self.assertEqual(settings.rest_interval, 20, "低于下限应回落默认值")
        self.assertEqual(settings.rest_opacity, 100, "高于上限应裁剪到上限")
        self.assertEqual(settings.blink_duration, 2.0, "低于下限应回落默认值")

    def test_wrong_types_are_ignored(self):
        settings = Settings.from_dict(
            {"rest_interval": "20", "autostart": "true", "paused": 1}
        )
        self.assertEqual(settings.rest_interval, 20)
        self.assertTrue(settings.autostart)
        self.assertFalse(settings.paused)

    def test_bool_is_not_accepted_as_number(self):
        self.assertEqual(Settings.from_dict({"rest_duration": True}).rest_duration, 20)

    def test_unknown_keys_do_not_crash(self):
        settings = Settings.from_dict({"legacy_option": 1, "rest_interval": 15})
        self.assertEqual(settings.rest_interval, 15)

    def test_json_roundtrip(self):
        original = Settings(rest_interval=25, blink_opacity=60, paused=True)
        restored = Settings.from_json(original.to_json())
        self.assertEqual(original.to_dict(), restored.to_dict())


class ConfigManagerTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmpdir.name, "config.json")
        self.manager = ConfigManager(self.path)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_missing_file_returns_defaults(self):
        self.assertFalse(os.path.exists(self.path))
        self.assertEqual(self.manager.settings.rest_interval, 20)

    def test_save_then_load(self):
        self.manager.save(Settings(rest_interval=42, paused=True))
        reloaded = ConfigManager(self.path).settings
        self.assertEqual(reloaded.rest_interval, 42)
        self.assertTrue(reloaded.paused)

    def test_save_is_atomic_no_temp_left(self):
        self.manager.save(Settings())
        leftovers = [n for n in os.listdir(self.tmpdir.name) if n != "config.json"]
        self.assertEqual(leftovers, [])
        with open(self.path, encoding="utf-8") as f:
            self.assertIn("rest_interval", json.load(f))

    def test_corrupted_file_degrades_to_defaults(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write('{"rest_interval": 30, ')
        self.assertEqual(self.manager.load().rest_interval, 20)

    def test_load_accepts_legacy_partial_json(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"rest_interval": 15, "blink_interval": 30}, f)
        settings = self.manager.load()
        self.assertEqual(settings.rest_interval, 15)
        self.assertFalse(settings.paused)

    def test_update_ignores_unknown_keys(self):
        self.manager.update(rest_interval=12, not_a_field=1)
        self.assertEqual(self.manager.settings.rest_interval, 12)
        self.assertFalse(hasattr(self.manager.settings, "not_a_field"))


if __name__ == "__main__":
    unittest.main()
