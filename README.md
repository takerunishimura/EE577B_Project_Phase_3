# EE577B Project Phase 3 — 16-Core Cardinal Chip Multiprocessor

**University of Southern California | EE577B Spring 2026 | Group 14**

---

## Overview

This repository contains the RTL design and verification of a 16-core Cardinal Chip Multiprocessor (CMP), organized as a 4×4 mesh Network-on-Chip. Each node consists of one Cardinal Processor (Phase 2), one Cardinal NIC, and one Cardinal Router (Phase 1). All 16 nodes are connected via the mesh NoC and verified with an all-to-all communication testbench achieving 240/240 packet delivery.

A torus topology extension was also implemented by adding wrap-around links across all 12 boundary nodes, reducing average completion time compared to the baseline mesh.

---

## Architecture

```
cardinal_cmp (top-level)
└── 16× node (cardinal_cpu + cardinal_nic + cardinal_router)
    └── cardinal_mesh (4×4 router interconnect)
```

Each node:
- **cardinal_cpu** — 64-bit 4-stage pipelined Cardinal Processor
- **cardinal_nic** — Network Interface Component bridging processor and router
- **cardinal_router** — 5-port router with XY-routing and credit-based flow control

---

## Key Design Features

- **XY dimension-order source routing** — packets carry hop count and direction fields; deadlock-free by construction
- **Credit-based flow control** — send/receive interleaving prevents deadlock under full load
- **All-to-all testbench** — each of 16 processors sends one packet to all other 15; verified 240/240 delivery
- **Torus extension** — wrap-around interconnects added to all 12 boundary nodes; validated 240/240 all-to-all
- **NIC virtual channel support** — NIC decodes the vc field and injects packets into the correct virtual channel
- Fully synthesizable RTL (no delays in design, delays only in testbench)
- Simulation clock: 4ns (250 MHz)

---

## Results

| Topology | All-to-All Packets Delivered | Completion (cycles) |
|---|---|---|
| Mesh | 240 / 240 | ~870 |
| Torus | 240 / 240 | ~845 |

---

## File Structure

```
EE577B_Project_Phase_3/
├── cmp/
│   ├── design/           # Top-level CMP .v files (cardinal_cmp.v, cardinal_mesh.v)
│   ├── tb/               # Full system testbench (tb_cardinal_cmp.v)
│   ├── testcase/         # Assembly and memory init/dump files (.fill, .dump)
│   ├── ref_test_cases/   # Reference test cases
│   ├── include/
│   ├── scripts/
│   ├── src/
│   ├── report/
│   └── work/
├── processor/
│   ├── design/           # Cardinal processor .v files
│   ├── tb/
│   ├── include/
│   ├── scripts/
│   ├── src/
│   ├── netlist/
│   ├── report/
│   ├── reports/
│   └── work/
├── router/
│   ├── design/           # Router .v files
│   ├── tb/
│   ├── include/
│   ├── scripts/
│   ├── src/
│   ├── netlist/
│   ├── report/
│   ├── reports/
│   └── work/
├── mesh/
│   ├── design/
│   ├── tb/
│   ├── include/
│   ├── scripts/
│   ├── src/
│   ├── netlist/
│   ├── report/
│   ├── reports/
│   └── work/
├── nic/
│   ├── design/           # NIC .v files
│   ├── tb/
│   ├── include/
│   ├── scripts/
│   ├── src/
│   ├── netlist/
│   ├── report/
│   ├── reports/
│   └── work/
├── .gitignore
└── README.md
```

---

## Tools

- **Simulation:** Cadence NC-Sim, Cadence SimVision
- **HDL:** Verilog (synthesizable style)

---

## Work Division

| Task | Owner |
|---|---|
| Cardinal NIC design | Tak |
| D-frontier v1/v2, send/receive interleaving deadlock fix | Tak |
| Torus topology extension | Tak |
| CMP integration (`cardinal_cmp.v`) | Tak & Alexandra |
| All-to-all testbench | Tak & Alexandra |
| Assembly program (`.asm`, `.fill` files) | Alexandra |
