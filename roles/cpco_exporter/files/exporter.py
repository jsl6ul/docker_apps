#!/usr/bin/env python3
"""
Prometheus exporter for Carel C.pCO controllers (MCDU-4U-T) — Modbus TCP only.

All metrics come from three read-only Modbus requests on one socket:
  FC04 input regs @1 x50   — live process image (doc "Read" idx 84..133)
  FC03 holding regs @1 x83 — setpoints (doc idx 1..83)
  FC01 coils       @45 x63 — unit state + alarm status (doc idx 45..107)

If a target's Modbus scrape fails (timeout, connection refused, ...),
/metrics answers HTTP 502 so the Prometheus scraper records the
instance as down (up 0, scrape_error 1) instead of ingesting a
cdu_up 0 sample from a healthy HTTP 200.

Register map (modbus.md, COMM VERSION 1.1) vs. empirical behavior:
  * The doc lists the Read process values as holding registers 4xxxx,
    but the controller exposes them as FC04 INPUT registers with
    address = doc index - 83 (doc idx 90 PSP -> input reg 7, verified
    against the HMI: 329.x kPa live).
  * FC03 holding of the same doc indices is frozen/stale — do not use.
  * Coils: FC01 register = doc index (the doc's "Modbus Register" column
    is off by one; alignment proven by the enable-default bits).
  * Raw register format: signed int16, fixed-point x10, SI units
    (kPa, degC, L/min, %), except integer/coded registers (scale 1.0).
    The machine UoM zone is SI; pressure process values/setpoints are
    kPa, converted to PSI. Registers are signed — with the secondary
    loop empty, SSP_1/SSP_2 read -0.6 kPa (raw 65530 as signed -6).
  * SDT is 0 in both candidate registers while the HMI shows a cached
    value, so it is derived here as SRT - SST.

Usage:
    ./exporter.py --host 192.168.10.62
    ./exporter.py --host 192.168.10.62 --listen-port 9100
"""

import argparse
import logging
import socket
import struct
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs, urlparse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cdu_exporter")

KPA_TO_PSI = 0.1450377

# ---------------------------------------------------------------------------
# Register maps. Scales: 0.1 = fixed-point x10 (doc "Real"), 1.0 = integer.
# ---------------------------------------------------------------------------

# FC04 input registers: addr = doc idx - 83. Live process image.
INPUT_ADDR = 1
INPUT_QTY = 50  # input regs 1..50 = doc idx 84..133
INPUT_VARS = [
    # (doc_idx, prom_label, help, scale, converter)
    (84,  "Pmp_1_Spd_Cmd", "Pump 1 speed command (%)",           0.1, None),
    (85,  "Pmp_1_RPM",     "Pump 1 RPM",                         1.0, None),
    (86,  "Pmp_1_Hours",   "Pump 1 run hours",                   1.0, None),
    (87,  "Pmp_2_Spd_Cmd", "Pump 2 speed command (%)",           0.1, None),
    (88,  "Pmp_2_RPM",     "Pump 2 RPM",                         1.0, None),
    (89,  "Pmp_2_Hours",   "Pump 2 run hours",                   1.0, None),
    (90,  "PSP",           "Primary supply pressure (PSI)",      0.1, lambda v: v * KPA_TO_PSI),
    (91,  "Pri_Flow",      "Primary flow (L/min)",               0.1, None),
    (92,  "PST",           "Primary supply temperature (C)",     0.1, None),
    (93,  "SSP_1",         "Secondary supply pressure 1 (PSI)",          0.1, lambda v: v * KPA_TO_PSI),
    (94,  "SSP_2",         "Secondary supply pressure 2 (PSI)",          0.1, lambda v: v * KPA_TO_PSI),
    (95,  "SSP",           "Active secondary supply pressure (PSI)",     0.1, lambda v: v * KPA_TO_PSI),
    (96,  "SRP_1",         "Secondary return pressure 1 (PSI)",          0.1, lambda v: v * KPA_TO_PSI),
    (97,  "SRP_2",         "Secondary return pressure 2 (PSI)",          0.1, lambda v: v * KPA_TO_PSI),
    (98,  "SRP",           "Active secondary return pressure (PSI)",     0.1, lambda v: v * KPA_TO_PSI),
    (99,  "Sec_DP",        "Secondary differential pressure (PSI)",      0.1, lambda v: v * KPA_TO_PSI),
    (100, "Sec_Flow",      "Secondary flow (L/min)",               0.1, None),
    (101, "SST_1_C",       "Secondary supply temp 1 (C)",          0.1, None),
    (102, "SST_2_C",       "Secondary supply temp 2 (C)",          0.1, None),
    (103, "SST_C",         "Active secondary supply temp (C)",     0.1, None),
    (104, "SRT_C",         "Active secondary return temp (C)",     0.1, None),
    (105, "Act_SST_SP",    "Active secondary supply temp setpoint (C)",  0.1, None),
    (106, "CW_Vlv_1_Out",  "Chilled water valve 1 command (%)",    0.1, None),
    (107, "CW_Vlv_1_FB",   "Chilled water valve 1 feedback (%)",   0.1, None),
    (108, "Rm_T_1",        "Room temperature 1 (C)",               0.1, None),
    (109, "Rm_Rh_1",       "Room relative humidity 1 (%)",         0.1, None),
    (110, "Rm_DewP_1_C",   "Room dew point 1 (C)",                 0.1, None),
    (111, "Rm_T_2",        "Room temperature 2 (C)",               0.1, None),
    (112, "Rm_Rh_2",       "Room relative humidity 2 (%)",         0.1, None),
    (113, "Rm_DewP_2_C",   "Room dew point 2 (C)",                 0.1, None),
    (114, "Rm_T",          "Active room temperature (C)",          0.1, None),
    (115, "Rm_Rh",         "Active room relative humidity (%)",    0.1, None),
    (116, "Rm_DewP",       "Active room dew point (C)",            0.1, None),
    (117, "UnitStatus",    "Unit status code (2 observed = off by alarm)", 1.0, None),
    (123, "Model",         "Model code",                           1.0, None),
    (132, "Sec_kW",        "Secondary cooling capacity (kW)",      0.1, None),
    (133, "Unit_Hours",    "Unit run hours",                       1.0, None),
]

# FC03 holding registers: addr = doc idx. Setpoints (live, SI x10).
HOLDING_ADDR = 1
HOLDING_QTY = 83  # holding regs 1..83
HOLDING_VARS = [
    (1,   "SST_SP",            "Secondary supply temp setpoint (C)",        0.1, None),
    (15,  "Sec_DP_SP",         "Secondary differential pressure setpoint (PSI)", 0.1, lambda v: v * KPA_TO_PSI),
    (20,  "Sec_Flow_SP",       "Secondary flow setpoint (L/min)",           0.1, None),
    (25,  "Min_Pump_Speed",    "Minimum pump speed (%)",                    0.1, None),
    (26,  "Max_Pump_Speed",    "Maximum pump speed (%)",                    0.1, None),
    (38,  "SSP_Lim_SP",        "Secondary supply pressure limit setpoint (PSI)", 0.1, lambda v: v * KPA_TO_PSI),
    (43,  "SSphiLim_Alm_SP",   "Sec supply pressure high limit alarm SP (PSI)", 0.1, lambda v: v * KPA_TO_PSI),
    (50,  "Low_SRP_Alm_SP",    "Low sec return pressure alarm SP (PSI)",    0.1, lambda v: v * KPA_TO_PSI),
    (52,  "Hi_PSP_Alm_SP",     "High primary supply pressure alarm SP (PSI)", 0.1, lambda v: v * KPA_TO_PSI),
    (54,  "Low_SST_Alm_SP",    "Low SST alarm setpoint (offset below SST_SP, C)", 0.1, None),
    (56,  "Hi_SST_Alm_SP",     "High SST alarm setpoint (offset above SST_SP, C)", 0.1, None),
    (58,  "Low_PST_Alm_SP",    "Low primary supply temp alarm SP (C)",      0.1, None),
    (60,  "Hi_PST_Alm_SP",     "High primary supply temp alarm SP (C)",     0.1, None),
    (62,  "Low_RmT_Alm_SP",    "Low room temp alarm SP (C)",                0.1, None),
    (64,  "Hi_RmT_Alm_SP",     "High room temp alarm SP (C)",               0.1, None),
    (66,  "Low_RmH_Alm_SP",    "Low room humidity alarm SP (%)",            0.1, None),
    (68,  "Hi_RmH_Alm_SP",     "High room humidity alarm SP (%)",           0.1, None),
    (74,  "Hi_SST_SD_Alm_SP",  "High SST shutdown alarm SP (C)",            0.1, None),
]

# FC01 coils: register = doc idx. State + alarm status.
COIL_ADDR = 45
COIL_QTY = 63  # coil regs 45..107
COIL_VARS = [
    (45,  "UnitOn",               "Unit ON status (1 = running)"),
    (46,  "UnitOff",              "Unit OFF status (1 = commanded off)"),
    (47,  "Pmp_1_Cmd",            "Pump 1 command (1 = on)"),
    (48,  "Pmp_1_RPM_Alarm",      "Pump 1 RPM alarm"),
    (49,  "Pmp_2_Cmd",            "Pump 2 command (1 = on)"),
    (50,  "Pmp_2_RPM_Alarm",      "Pump 2 RPM alarm"),
    (51,  "CDUR_Sts",             "CDU ready status"),
    (52,  "PA_Sts",               "PLC alive status"),
    (53,  "Global_Alarm",         "Global alarm (1 = any alarm active)"),
    (55,  "Critical_Alarm",       "Critical alarm"),
    (56,  "WDS_1_Alarm",          "Water detection sensor 1 alarm"),
    (57,  "WDS_2_Alarm",          "Water detection sensor 2 alarm"),
    (58,  "WDS_Stop_Alarm",       "Water detection alarm, CDU off"),
    (59,  "Al_Flow_Pump_1",       "Pump 1 low flow alarm"),
    (60,  "Al_DP_Pump_1",         "Pump 1 low differential pressure alarm"),
    (61,  "Pmp1_Man_D_Wng",       "Pump 1 manual disable warning"),
    (62,  "Al_Flow_Pump_2",       "Pump 2 low flow alarm"),
    (63,  "Al_DP_Pump_2",         "Pump 2 low differential pressure alarm"),
    (64,  "Pmp2_Man_D_Wng",       "Pump 2 manual disable warning"),
    (65,  "CW_Vlv_1_FB_Alarm",    "CW valve 1 feedback alarm"),
    (68,  "PST_Alarm",            "Primary supply temp probe alarm"),
    (69,  "Low_PST_Alarm",        "Low primary supply temp alarm"),
    (70,  "Hi_PST_Alarm",         "High primary supply temp alarm"),
    (71,  "SST_1_Alarm",          "Secondary supply temp 1 probe alarm"),
    (72,  "SST_2_Alarm",          "Secondary supply temp 2 probe alarm"),
    (73,  "SST_Alarm",            "Secondary supply temp alarm, CDU off"),
    (74,  "SST_DEV_Warning",      "Sec supply temp probe deviation warning"),
    (75,  "Low_SST_Alarm",        "Low secondary supply temp alarm"),
    (76,  "Hi_SST_Alarm",         "High secondary supply temp alarm"),
    (77,  "SRT_Alarm",            "Secondary return temp probe alarm"),
    (78,  "RmS_1_Comm_Alarm",     "Room sensor 1 communication alarm"),
    (79,  "RmT_1_Alm",            "Room temp sensor 1 alarm"),
    (80,  "RmH_1_Alm",            "Room humidity sensor 1 alarm"),
    (81,  "RmT_2_Alm",            "Room temp sensor 2 alarm"),
    (82,  "RmH_2_Alm",            "Room humidity sensor 2 alarm"),
    (84,  "Dew_Point_Warning",    "High dewpoint warning"),
    (85,  "Dew_Point_Alarm",      "High dewpoint alarm"),
    (86,  "Dew_P_S_Alarm",        "Dewpoint sensor alarm, CDU off"),
    (87,  "Dew_Point_Stop_Alarm", "High dewpoint stop alarm, CDU off"),
    (88,  "DPS_DEV_Warning",      "Dewpoint sensor probe deviation warning"),
    (89,  "Low_RmT_Alarm",        "Low room temp alarm"),
    (90,  "Hi_RmT_Alarm",         "High room temp alarm"),
    (91,  "Low_RmH_Alarm",        "Low room humidity alarm"),
    (92,  "Hi_RmH_Alarm",         "High room humidity alarm"),
    (93,  "PSP_Alarm",            "Primary supply pressure probe alarm"),
    (94,  "Hi_PSP_Alarm",         "High primary supply pressure alarm"),
    (95,  "Pri_Flow_Alarm",       "Primary flow meter alarm"),
    (96,  "SSP_1_Alarm",          "Secondary supply pressure 1 probe alarm"),
    (97,  "SSP_2_Alarm",          "Secondary supply pressure 2 probe alarm"),
    (98,  "SSP_DEV_Warning",      "Sec supply pressure probe deviation warning"),
    (99,  "SSphiLim_Alarm",       "Sec supply pressure high limit alarm"),
    (100, "SRP_1_Alarm",          "Secondary return pressure 1 probe alarm"),
    (101, "SRP_2_Alarm",          "Secondary return pressure 2 probe alarm"),
    (102, "SRP_DEV_Warning",      "Sec return pressure probe deviation warning"),
    (103, "Low_SRP_Alarm",        "Low secondary return pressure alarm"),
    (104, "Sec_Flow_Alarm",       "Secondary flow meter alarm"),
    (105, "Hi_SST_SD_Alarm",      "High SST shutdown alarm"),
    (106, "Sec_Flow_Stop_Alarm",  "Sec flow stop alarm, CDU off"),
    (107, "Sys_DP_Stop_Alarm",    "System DP stop alarm, CDU off"),
]


# ---------------------------------------------------------------------------
# Modbus TCP
# ---------------------------------------------------------------------------
def _mb_transact(s, pdu):
    """Send one Modbus TCP request on an open socket; returns response body."""
    s.sendall(struct.pack(">HHHB", 1, 0, len(pdu) + 1, 1) + pdu)
    hdr = b""
    while len(hdr) < 7:
        chunk = s.recv(7 - len(hdr))
        if not chunk:
            raise OSError("modbus: connection closed")
        hdr += chunk
    _, _, rlen, _ = struct.unpack(">HHHB", hdr)
    body = b""
    while len(body) < rlen - 1:
        chunk = s.recv(rlen - 1 - len(body))
        if not chunk:
            raise OSError("modbus: connection closed")
        body += chunk
    if body[0] & 0x80:
        raise OSError(f"modbus exception code {body[1]}")
    return body


def _mb_regs(s, func, addr, qty):
    """FC03/FC04 read; returns register values as signed int16."""
    body = _mb_transact(s, struct.pack(">BHH", func, addr, qty))
    n = body[1] // 2
    return struct.unpack(f">{n}h", body[2:2 + 2 * n])


def _mb_coils(s, addr, qty):
    """FC01 read; returns list of 0/1 coil values (bit i in byte i//8)."""
    body = _mb_transact(s, struct.pack(">BHH", 1, addr, qty))
    raw = body[2:2 + body[1]]
    return [(raw[i // 8] >> (i % 8)) & 1 for i in range(qty)]


def scrape_modbus(host, port, timeout=10):
    """Read process image + setpoints + state coils.

    Returns (values, up, err); err is a short failure description ("" if ok).
    """
    values = {}
    up = 0
    err = ""
    try:
        s = socket.create_connection((host, port), timeout=timeout)
    except (OSError, socket.timeout) as exc:
        err = f"connect {host}:{port} failed: {exc}"
        log.warning(err)
        return values, up, err
    try:
        with s:
            inputs = _mb_regs(s, 4, INPUT_ADDR, INPUT_QTY)
            for idx, label, _h, scale, conv in INPUT_VARS:
                v = inputs[idx - 83 - INPUT_ADDR] * scale
                values[label] = conv(v) if conv else v

            holdings = _mb_regs(s, 3, HOLDING_ADDR, HOLDING_QTY)
            for idx, label, _h, scale, conv in HOLDING_VARS:
                v = holdings[idx - HOLDING_ADDR] * scale
                values[label] = conv(v) if conv else v

            coils = _mb_coils(s, COIL_ADDR, COIL_QTY)
            for idx, label, _h in COIL_VARS:
                values[label] = float(coils[idx - COIL_ADDR])

            if "SST_C" in values and "SRT_C" in values:
                values["SDT"] = values["SRT_C"] - values["SST_C"]

            up = 1
    except (OSError, socket.timeout) as exc:
        err = f"scrape {host}:{port} failed: {exc}"
        log.warning(err)
    return values, up, err


def metric_name(var_label):
    """Sanitise a label for Prometheus metric naming."""
    return var_label.replace("-", "_").replace(".", "_").replace(" ", "_")


def _fmt(value, scale):
    if scale == 1.0:
        return str(int(value))
    return f"{value:.2f}"


def render_metrics(values, up, duration):
    """Build Prometheus text-expo format string."""
    lines = []

    lines.append("# HELP cdu_up Whether the last Modbus scrape of the CDU succeeded.")
    lines.append("# TYPE cdu_up gauge")
    lines.append(f"cdu_up {int(up)}")

    lines.append("# HELP cdu_scrape_duration_seconds Seconds spent scraping the CDU.")
    lines.append("# TYPE cdu_scrape_duration_seconds gauge")
    lines.append(f"cdu_scrape_duration_seconds {duration:.3f}")

    defs = (
        [(label, help_text, scale) for _i, label, help_text, scale, _c in INPUT_VARS]
        + [(label, help_text, scale) for _i, label, help_text, scale, _c in HOLDING_VARS]
        + [(label, help_text, 1.0) for _i, label, help_text in COIL_VARS]
        + [("SDT", "Secondary differential temp, derived (SRT - SST) (C)", 0.1)]
    )
    for label, help_text, scale in defs:
        mn = metric_name(label)
        lines.append(f"# HELP cdu_{mn} {help_text}")
        lines.append(f"# TYPE cdu_{mn} gauge")
        val = values.get(label)
        lines.append(
            f"cdu_{mn} {_fmt(val, scale)}" if val is not None else f"cdu_{mn} NaN"
        )

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------
class ExporterHandler(BaseHTTPRequestHandler):
    server_version = "CDUExporter/1.0"

    def log_message(self, fmt, *args):
        log.debug(fmt, *args)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._respond(200, "text/plain", "ok\n")
            return

        if parsed.path != "/metrics":
            self._respond(404, "text/plain", "Not found\n")
            return

        qs = parse_qs(parsed.query)
        targets = qs.get("target", [cli_args.host])

        t0 = time.monotonic()
        results = {}
        ups = {}
        errs = {}

        with ThreadPoolExecutor(max_workers=min(len(targets), 32)) as pool:
            futs = {
                pool.submit(scrape_modbus, t, cli_args.modbus_port, cli_args.timeout): t
                for t in targets
            }
            for fut in as_completed(futs):
                host = futs[fut]
                try:
                    results[host], ups[host], errs[host] = fut.result()
                except Exception as exc:
                    log.error("scrape thread error for %s: %s", host, exc)
                    results[host], ups[host], errs[host] = {}, 0, str(exc)

        duration = time.monotonic() - t0

        # Fail the scrape so Prometheus marks the instance down (up 0,
        # scrape_error 1) instead of ingesting cdu_up 0 as a healthy sample.
        failed = [h for h in targets if not ups[h]]
        if failed:
            detail = "; ".join(f"{h}: {errs[h]}" for h in failed)
            self._respond(502, "text/plain; charset=utf-8",
                          f"CDU scrape failed: {detail}\n")
            return

        parts = [
            render_metrics(results[h], ups[h], duration) for h in targets
        ]
        self._respond(200, "text/plain; charset=utf-8", "\n".join(parts))

    def _respond(self, code, ct, body):
        self.send_response(code)
        self.send_header("Content-Type", ct)
        # Allow the custom cdu.htm page (served by the controller) to poll
        # this exporter from the browser.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Each Prometheus scrape runs in its own daemon thread."""

    daemon_threads = True
    allow_reuse_address = True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prometheus exporter for MCDU-4U-T (Modbus TCP only)"
    )
    parser.add_argument(
        "--host",
        default="",
        help="Target CDU host (override via ?target= at scrape time)",
    )
    parser.add_argument(
        "--modbus-port", type=int, default=502,
        help="CDU Modbus TCP port (default 502)",
    )
    parser.add_argument(
        "--listen-port",
        type=int,
        default=9340,
        help="Exporter listen port (default 9340)",
    )
    parser.add_argument(
        "--listen-host",
        default="0.0.0.0",
        help="Exporter bind address (default 0.0.0.0)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Modbus timeout per CDU scrape in seconds (default 10)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging"
    )

    cli_args = parser.parse_args()

    if cli_args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    server = ThreadingHTTPServer(
        (cli_args.listen_host, cli_args.listen_port), ExporterHandler
    )
    n_metrics = len(INPUT_VARS) + len(HOLDING_VARS) + len(COIL_VARS) + 1
    log.info(
        "Listening on %s:%d  (targets via --host or ?target=, %d metrics)",
        cli_args.listen_host,
        cli_args.listen_port,
        n_metrics,
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down")
        server.shutdown()
