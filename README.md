# Display Link Lab

[![CI](https://github.com/bebequ/display-link-lab/actions/workflows/test.yml/badge.svg)](https://github.com/bebequ/display-link-lab/actions/workflows/test.yml)

A small, vendor-neutral toolkit for embedded display engineering. The first utility is a MIPI DSI link-budget estimator.

A vendor-neutral Python tool for estimating average MIPI DSI active-pixel payload and an explicitly assumed per-lane HS data-rate requirement. Intended as a public-safe embedded-display engineering sample, **not** a production panel driver or PHY validator.

## Quick start

Python 3.10+; no third-party dependencies.

    python3 dsi_budget.py --width 1280 --height 720 --refresh 60 --bpp 24 --lanes 4
    python3 dsi_budget.py --width 1280 --height 720 --refresh 60 --bpp 24 --lanes 4 --traffic-multiplier 1.1 --efficiency 0.85 --lane-limit-mbps 500 --json
    python3 -m unittest discover -s tests -v

The 1280 × 720, 60 Hz, RGB888 example produces **1,327.104 Mb/s** of active-pixel payload, or **331.776 Mb/s per lane** for four data lanes before accounting for any non-active overhead.

## Explicit model

    active_payload_bps = width * height * refresh_hz * bits_per_pixel
    modeled_required_bps = active_payload_bps * traffic_multiplier / efficiency
    modeled_per_lane_bps = modeled_required_bps / lanes

- Traffic multiplier (>= 1) models additional non-active traffic *as a user assumption*. It is **not** inferred from blanking or DSI packet framing.
- Efficiency (0 < value <= 1) represents assumed usable HS capacity. Its default 1.0 exposes a lower bound, **not** a claim of perfect real-world efficiency.
- Lane limit is a user-supplied scenario ceiling. Exit status 1 means the estimate exceeds that ceiling; exit status 2 indicates invalid CLI input.
- The calculator reports the *average* requirement, not the peak burst rate.

## Not a hardware signoff

This calculator does not derive DSI video-mode packetization, ECC/CRC overhead, blanking, LP/HS transitions, virtual-channel arbitration, command-mode burst peaks, PHY setup/hold, cable impedance, deskew, eye diagram, D-PHY version support, or signal-integrity margin. Real feasibility depends on the SoC, bridge/panel datasheets, exact timing, and hardware validation.

## Open-source contribution candidates

1. Add public, documented DSI video-mode traffic scenarios with tests.
2. Add a supported public-device fixture and independently reproducible measured-vs-estimated comparison.
3. Use the GitHub PR process for small, test-backed changes.

## Provenance and boundaries

Written as an independent, generic educational sample. It does not contain company-owned source, private firmware, customer records, or proprietary register tables.

## Contributing

Reproducible issue reports, tests, and small pull requests are welcome. Please do not submit proprietary source, private hardware register values, or customer information. Include the assumptions and test command with any calculation change.

## License

MIT; see [LICENSE](LICENSE).
