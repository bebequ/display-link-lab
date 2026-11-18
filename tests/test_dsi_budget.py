import math
import unittest

from dsi_budget import estimate


class BudgetTests(unittest.TestCase):
    def test_active_payload_720p60_rgb888(self):
        result = estimate(1280, 720, 60, 24, 4)
        self.assertAlmostEqual(result.active_payload_mbps, 1327.104)
        self.assertAlmostEqual(result.modeled_per_lane_mbps, 331.776)
        self.assertAlmostEqual(result.modeled_burst_per_lane_mbps, 331.776)
        self.assertIsNone(result.within_lane_limit)
        self.assertIsNone(result.modeled_max_refresh_hz)

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

    def test_hs_window_can_change_scenario_verdict(self):
        average_only = estimate(1280, 720, 60, 24, 4, 1.1, 0.85, 500)
        with_hs_window = estimate(1280, 720, 60, 24, 4, 1.1, 0.85, 500, 0.8)
        self.assertTrue(average_only.within_lane_limit)
        self.assertFalse(with_hs_window.within_lane_limit)
        self.assertAlmostEqual(with_hs_window.modeled_per_lane_mbps,
                               average_only.modeled_per_lane_mbps)
        self.assertAlmostEqual(with_hs_window.modeled_burst_per_lane_mbps,
                               average_only.modeled_per_lane_mbps / 0.8)

    def test_inverse_refresh_matches_rate_ceiling(self):
        config = dict(width=1280, height=720, refresh_hz=60, bits_per_pixel=24,
                      lanes=4, traffic_multiplier=1.1, efficiency=0.85,
                      lane_limit_mbps=500, hs_window_fraction=0.8)
        original = estimate(**config)
        self.assertLess(original.modeled_max_refresh_hz, 60)
        config["refresh_hz"] = original.modeled_max_refresh_hz
        at_ceiling = estimate(**config)
        self.assertAlmostEqual(at_ceiling.modeled_burst_per_lane_mbps, 500)

    def test_hs_window_monotonic(self):
        params = dict(width=640, height=480, refresh_hz=60, bits_per_pixel=24,
                      lanes=2, lane_limit_mbps=500)
        full_window = estimate(**params, hs_window_fraction=1)
        half_window = estimate(**params, hs_window_fraction=0.5)
        self.assertAlmostEqual(half_window.modeled_burst_per_lane_mbps,
                               2 * full_window.modeled_burst_per_lane_mbps)
        self.assertAlmostEqual(half_window.modeled_max_refresh_hz,
                               full_window.modeled_max_refresh_hz / 2)

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
                       {"lane_limit_mbps": math.nan},
                       {"hs_window_fraction": 0},
                       {"hs_window_fraction": -0.1},
                       {"hs_window_fraction": 1.1},
                       {"hs_window_fraction": math.nan},
                       {"hs_window_fraction": math.inf}):
            params = dict(width=640, height=480, refresh_hz=60,
                          bits_per_pixel=24, lanes=4)
            params.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                estimate(**params)


if __name__ == "__main__":
    unittest.main()
