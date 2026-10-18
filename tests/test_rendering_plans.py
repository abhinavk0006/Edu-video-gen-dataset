"""Guard atomic shot planning and per-step duration defaults."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_rag_prompt_bundle import normalize_step, requires_clip_split


class RenderingPlanTests(unittest.TestCase):
    def test_addition_and_paper_observation_require_separate_shots(self):
        self.assertTrue(requires_clip_split("Add the reagent and hold litmus paper above the tube."))
        self.assertTrue(requires_clip_split("Add water and swirl the tube."))
        self.assertFalse(requires_clip_split("Add water to dissolve the salt."))

    def test_experiment_total_is_not_reused_as_each_shot_duration(self):
        record = {"status": "reviewed", "estimated_video_duration_seconds": 240}
        step = {"step_id": 1, "instruction": "Add water slowly", "observation": "The solution is clear"}
        self.assertEqual(normalize_step(record, {}, step, None)["duration_seconds"], 2.0)
        self.assertEqual(normalize_step(record, {}, {**step, "duration_seconds": 4.5}, None)["duration_seconds"], 4.5)


if __name__ == "__main__":
    unittest.main()
