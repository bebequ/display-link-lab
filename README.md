# Display Link Lab

[![Python CI](https://github.com/bebequ/display-link-lab/actions/workflows/test.yml/badge.svg)](https://github.com/bebequ/display-link-lab/actions/workflows/test.yml)

Small, vendor-neutral, test-backed tools for embedded-display engineering.

The first tool, `dsi_budget.py`, estimates the average active-pixel payload and a **scenario-based** per-lane HS rate for MIPI DSI. It deliberately separates what is mathematically certain from what must be measured or specified for real hardware.

## Quick start

Python 3.10+; no third-party dependencies.

```sh
python3 dsi_budget.py --width 1280 --height 720 --refresh 60 --bpp 24 --lanes 4
python3 dsi_budget.py --width 1280 --height 720 --refresh 60 --bpp 24 --lanes 4 \
    --traffic-multiplier 1.1 --efficiency 0.85 --hs-window-fraction 0.8 \
    --lane-limit-mbps 500 --json
python3 -m unittest discover -s tests -v
```

The baseline 1280 × 720 × 60 Hz × RGB888 active-pixel payload is **1,327.104 Mb/s**, or **331.776 Mb/s per lane** for four lanes, before assumed overhead and traffic-window constraints.

## What the model calculates

```text
active_payload_mbps = width × height × refresh_hz × bits_per_pixel / 1e6
modeled_total_mbps = active_payload_mbps × traffic_multiplier / efficiency
modeled_avg_per_lane_mbps = modeled_total_mbps / lanes
modeled_burst_per_lane_mbps = modeled_avg_per_lane_mbps / hs_window_fraction
modeled_max_refresh_hz = refresh_hz × lane_limit_mbps / modeled_burst_per_lane_mbps
```

All assumptions are user-supplied:

| Input | Default | Interpretation |
| --- | ---: | --- |
| `traffic_multiplier` | 1.0 | Assumed additional transmitted traffic (at least 1). **Not calculated** from DSI packets or blanking |
| `efficiency` | 1.0 | Assumed usable share of HS capacity (0, 1]. 1.0 is a lower-bound planning assumption |
| `hs_window_fraction` | 1.0 | Assumed portion of a frame during which the modeled traffic can be transmitted at HS (0, 1]. 1.0 allows the entire frame |
| `lane_limit_mbps` | omitted | User-provided ceiling for one D-PHY data lane; not an inferred hardware specification |

The lane utilization and within-limit result compare the **modeled burst rate**, not merely the average rate, with the assumed lane ceiling. The modeled maximum refresh rate is only returned when a ceiling is supplied. These are algebraic scenario estimates, **not verified device limits**.

For example, with the default assumptions, 331.776 Mb/s per lane is the averaged rate. Constraining transmission to 80% of the frame raises the modeled burst requirement to 414.720 Mb/s per lane even before any additional overhead. Without valid transport timing, the 80% value is hypothetical.

## Limitations

This tool does **not** calculate DSI packetization, ECC/CRC, blanking traffic, LP/HS mode transition timing, link overhead, command-mode peak bursts, virtual-channel arbitration, D-PHY setup/hold, deskew, signal integrity, eye opening, or board/cable losses. The active pixels are modeled with a fixed bits-per-pixel payload; actual protocols may encode/pack them differently. A scenario that passes the estimate may still fail on hardware.

Use public SoC/bridge/panel documentation and lab measurements to replace assumptions with evidence. Do not treat this utility as a hardware signoff or standards conformance test.

## Contributing

Small issues and pull requests with reproducible examples and tests are welcome. Include the chosen assumptions, expected result, and a command that checks it. Never include proprietary source, register maps, customer records, or confidential device information.

## License

MIT. See [LICENSE](LICENSE).
