#!/usr/bin/env python3
"""Estimate MIPI DSI active-pixel payload and assumed per-lane HS requirements.

This is a scenario calculator, NOT a DSI packet/timing or D-PHY signoff tool.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math


@dataclass(frozen=True)
class Budget:
    active_payload_mbps: float
    modeled_total_mbps: float
    modeled_per_lane_mbps: float
    modeled_burst_per_lane_mbps: float
    assumed_hs_window_fraction: float
    lane_limit_mbps: float | None
    utilization_pct: float | None
    within_lane_limit: bool | None
    modeled_max_refresh_hz: float | None


def estimate(width: int, height: int, refresh_hz: float, bits_per_pixel: int,
             lanes: int, traffic_multiplier: float = 1.0,
             efficiency: float = 1.0, lane_limit_mbps: float | None = None,
             hs_window_fraction: float = 1.0) -> Budget:
    """Model average and time-window-constrained HS rates.

    traffic_multiplier: user-assumed additional traffic, never auto-derived.
    efficiency: user-assumed usable fraction of HS throughput.
    hs_window_fraction: user-assumed portion of each frame available for
        transmitting all modeled traffic at HS rate; NOT a DSI timing calculation.
    """
    if not all(isinstance(x, int) and not isinstance(x, bool) and x > 0
               for x in (width, height, bits_per_pixel, lanes)):
        raise ValueError("width, height, bits_per_pixel and lanes must be positive integers")
    if lanes > 4:
        raise ValueError("this example models 1-4 D-PHY data lanes")
    for name, value in (("refresh_hz", refresh_hz),
                        ("traffic_multiplier", traffic_multiplier),
                        ("efficiency", efficiency),
                        ("hs_window_fraction", hs_window_fraction)):
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")
    if refresh_hz <= 0 or traffic_multiplier < 1 or not (0 < efficiency <= 1):
        raise ValueError("require refresh_hz > 0, traffic_multiplier >= 1, 0 < efficiency <= 1")
    if not (0 < hs_window_fraction <= 1):
        raise ValueError("hs_window_fraction must be in (0, 1]")
    if lane_limit_mbps is not None and (
            not math.isfinite(lane_limit_mbps) or lane_limit_mbps <= 0):
        raise ValueError("lane_limit_mbps must be finite and > 0")

    payload = width * height * refresh_hz * bits_per_pixel / 1_000_000
    total = payload * traffic_multiplier / efficiency
    per_lane = total / lanes
    burst = per_lane / hs_window_fraction
    if not all(math.isfinite(value) for value in (payload, total, per_lane, burst)):
        raise ValueError("calculated rates must be finite")
    utilization = None if lane_limit_mbps is None else 100 * burst / lane_limit_mbps
    within = None if lane_limit_mbps is None else burst <= lane_limit_mbps
    max_refresh = None if lane_limit_mbps is None else refresh_hz * lane_limit_mbps / burst
    return Budget(payload, total, per_lane, burst, hs_window_fraction,
                  lane_limit_mbps, utilization, within, max_refresh)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--refresh", type=float, required=True, help="frames per second")
    parser.add_argument("--bpp", type=int, required=True, help="transmitted payload bits per pixel")
    parser.add_argument("--lanes", type=int, required=True, help="1-4 D-PHY data lanes")
    parser.add_argument("--traffic-multiplier", type=float, default=1.0,
                        help="assumed traffic scaling (>=1), NOT inferred packet overhead")
    parser.add_argument("--efficiency", type=float, default=1.0,
                        help="assumed usable HS capacity fraction (0,1]")
    parser.add_argument("--hs-window-fraction", type=float, default=1.0,
                        help="assumed fraction of frame available for HS transfer (0,1]")
    parser.add_argument("--lane-limit-mbps", type=float,
                        help="assumed per-lane HS ceiling, Mb/s")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = estimate(args.width, args.height, args.refresh, args.bpp,
                          args.lanes, args.traffic_multiplier, args.efficiency,
                          args.lane_limit_mbps, args.hs_window_fraction)
    except ValueError as exc:
        parser.error(str(exc))

    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print(f"Active-pixel payload:   {result.active_payload_mbps:.3f} Mb/s total")
        print(f"Modeled requirement:    {result.modeled_total_mbps:.3f} Mb/s total")
        print(f"Modeled avg per lane:   {result.modeled_per_lane_mbps:.3f} Mb/s")
        print(f"Modeled HS per lane:    {result.modeled_burst_per_lane_mbps:.3f} Mb/s "
              f"(HS window {result.assumed_hs_window_fraction:.1%})")
        if result.lane_limit_mbps is not None:
            print(f"HS lane utilization:   {result.utilization_pct:.1f}% "
                  f"({'within' if result.within_lane_limit else 'OVER'} assumed limit)")
            print(f"Modeled max refresh:   {result.modeled_max_refresh_hz:.3f} Hz")
    return 1 if result.within_lane_limit is False else 0


if __name__ == "__main__":
    raise SystemExit(main())
