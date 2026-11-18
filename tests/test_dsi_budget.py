import math
import unittest

from dsi_budget import estimate


class BudgetTests(unittest.TestCase):
    def test_active_payload_720p60_rgb888(self):
        result = estimate(1280, 720, 60, 24, 4)
        self.assertAlmostEqual(result.active_payload_mbps, 1327.104)
        self.assertAlmostEqual(result.modeled_per_lane_mbps, 331.776)
        self.assertIsNone(result.within_lane_limit)

    def test_scenario_assumptions_are_explicit(self):
        result = estimate(1280, 720, 60, 24, 4, 1.1, 0.85, 500)
        self.assertAlmostEqual(result.modeled_per_lane_mbps, 429.35717647, places=4)
        self.assertTrue(result.within_lane_limit)
        self.assertAlmostEqual(result.utilization_pct, 85.87143529, places=4)

    def test_insufficient_lane_capacity(self):
        self.assertFalse(estimate(1280, 720, 60, 24, 4,
                                  lane_limit_mbps=300).within_lane_limit)

    def test_boundary_equal_limit_passes(self):
        self.assertTrue(estimate(1280, 720, 60, 24, 4,
                                 lane_limit_mbps=331.776).within_lane_limit)

    def test_lane_count_scales_rate(self):
        self.assertAlmostEqual(estimate(640, 480, 60, 24, 2).modeled_per_lane_mbps,
                               2 * estimate(640, 480, 60, 24, 4).modeled_per_lane_mbps)

    def test_reject_invalid_dimensions(self):
        for kwargs in ({"width": 0}, {"lanes": 5},
                       {"bits_per_pixel": 0}, {"height": -1}):
            params = dict(width=640, height=480, refresh_hz=60,
                          bits_per_pixel=24, lanes=4)
            params.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                estimate(**params)

    def test_reject_invalid_assumptions(self):
        for kwargs in ({"traffic_multiplier": 0.9}, {"efficiency": 0},
                       {"efficiency": 1.1}, {"refresh_hz": math.inf},
                       {"lane_limit_mbps": math.nan}):
            params = dict(width=640, height=480, refresh_hz=60,
                          bits_per_pixel=24, lanes=4)
            params.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                estimate(**params)


if __name__ == "__main__":
    unittest.main()
