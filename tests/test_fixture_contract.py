"""检查采集资料的身份、形状和可交叉引用性。"""

import json
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def read_fixture(name):
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


class FixtureContractTests(unittest.TestCase):
    def test_record_manifest(self):
        manifest = read_fixture("manifest.json")
        primary = read_fixture("primary.json")
        revision = read_fixture("revision.json")
        self.assertEqual(manifest["fixture"], "grasp_transport")
        self.assertEqual(manifest["records"], ["previous.json", "primary.json", "revision.json"])
        self.assertTrue(manifest["synthetic"])
        self.assertEqual(revision["replaces"], primary["capture"])
        self.assertNotEqual(revision["capture"], primary["capture"])

    def test_related_input_records(self):
        primary = read_fixture("primary.json")
        revision = read_fixture("revision.json")
        devices = {item["id"]: item for item in primary["devices"]}
        surfaces = {item["id"]: item for item in primary["surfaces"]}
        edge_ids = {(item["device"], item["surface"]) for item in primary["edges"]}
        for group in primary["shared_groups"]:
            self.assertFalse({tuple(edge) for edge in group["edges"]} - edge_ids)
            self.assertGreater(group["cap"], 0)
        for device, surface in edge_ids:
            self.assertIn(device, devices)
            self.assertIn(surface, surfaces)
        for device, surface, value in revision["training_read"]["edge_upstream"]:
            self.assertIn((device, surface), edge_ids)
            self.assertTrue(np.isfinite(value))

    def test_previous_generation_is_complete(self):
        previous = read_fixture("previous.json")
        primary = read_fixture("primary.json")
        self.assertEqual(primary["previous_generation"], previous["generation"])
        self.assertNotEqual(primary["capture"], previous["capture"])
        self.assertEqual(previous["devices"], primary["devices"])
        self.assertEqual(previous["surfaces"], primary["surfaces"])
        self.assertTrue(all(edge["status"] == "valid" for edge in previous["edges"]))
        self.assertTrue(any(edge["status"] == "pending_rephoto" for edge in primary["edges"]))
