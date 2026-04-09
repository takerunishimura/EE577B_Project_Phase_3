#!/usr/bin/env python3
"""
gen_torus_files.py
Generates all 32 memory init files for Phase 3 Cardinal CMP all-to-all test:
  - 16 imem files: cmp_test.imem.RC.fill (identical for all nodes)
  - 16 dmem files: cmp_test.dmem.RC.fill (unique per node)

Node layout (row, col):
  (0,0)=node00  (0,1)=node01  (0,2)=node02  (0,3)=node03
  (1,0)=node10  (1,1)=node11  (1,2)=node12  (1,3)=node13
  (2,0)=node20  (2,1)=node21  (2,2)=node22  (2,3)=node23
  (3,0)=node30  (3,1)=node31  (3,2)=node32  (3,3)=node33

Packet format (big-endian, bit[0] = MSB):
  bit[0]     = vc       (virtual channel: 0=even, 1=odd)
  bit[1]     = dirX     (0=East, 1=West)
  bit[2]     = dirY     (0=South, 1=North)
  bit[3:7]   = reserved (5 bits, set to 0)
  bit[8:11]  = hopX     (4-bit unary: N hops = (1<<N)-1, e.g. 2 hops = 0b0011)
  bit[12:15] = hopY     (4-bit unary)
  bit[16:23] = sourceX  (8-bit col of source)
  bit[24:31] = sourceY  (8-bit row of source)
  bit[32:63] = payload  (32-bit, we use source_id in upper 16 + dest_id in lower 16)

XY routing: route X first (East/West), then Y (North/South)
  dirX=1 (East):  shortest path goes right (or wraps)
  dirX=0 (West):  shortest path goes left (or wraps)
  dirY=0 (South): shortest path goes down (or wraps)
  dirY=1 (North): shortest path goes up (or wraps)

Unary hop encoding: N hops -> (1 << N) - 1
  0 hops -> 0b0000 = 0x0
  1 hop  -> 0b0001 = 0x1
  2 hops -> 0b0011 = 0x3
  3 hops -> 0b0111 = 0x7

NIC address map (memAddr[16]=memAddr[17]=1):
  0xC000 = input buffer
  0xC001 = input status
  0xC002 = output buffer
  0xC003 = output status

dmem layout per node:
  MEM[0..14]  = 15 outgoing packets (one per destination, in order)
  MEM[15]     = 0x0000000000000000 (sentinel)
  MEM[16..30] = 15 incoming packets stored here by receive loop
  MEM[31]     = 0x0000000000000000

Assembly program (same for all nodes, PC = instruction word index):
  Send phase: 15 blocks of 4 instructions each (PC 0-59)
    POLL_Si: VLD  r2, 0xC003      ; PC = i*4+0
             VBNEZ r2, POLL_Si    ; PC = i*4+1  (branch back to i*4)
             VLD  r1, i           ; PC = i*4+2
             VSD  r1, 0xC002      ; PC = i*4+3
  Recv phase: 15 blocks of 4 instructions each (PC 60-119)
    POLL_Ri: VLD  r2, 0xC001      ; PC = 60+i*4+0
             VBEZ  r2, POLL_Ri    ; PC = 60+i*4+1  (branch back to 60+i*4)
             VLD  r1, 0xC000      ; PC = 60+i*4+2
             VSD  r1, 16+i        ; PC = 60+i*4+3
  End: 4x VNOP at PC 120-123, then 0x00000000 at PC 124+
"""

import os

# ============================================================
# Instruction encoding helpers
# ============================================================

def vld(rD, imm):
    """VLD rD, imm: 100000 rD 00000 imm[0:15]"""
    return (0b100000 << 26) | (rD << 21) | (0 << 16) | (imm & 0xFFFF)

def vsd(rD, imm):
    """VSD rD, imm: 100001 rD 00000 imm[0:15]"""
    return (0b100001 << 26) | (rD << 21) | (0 << 16) | (imm & 0xFFFF)

def vbez(rD, imm):
    """VBEZ rD, imm: 100010 rD 00000 imm[0:15]"""
    return (0b100010 << 26) | (rD << 21) | (0 << 16) | (imm & 0xFFFF)

def vbnez(rD, imm):
    """VBNEZ rD, imm: 100011 rD 00000 imm[0:15]"""
    return (0b100011 << 26) | (rD << 21) | (0 << 16) | (imm & 0xFFFF)

def vnop():
    """VNOP: 111100 00000 00000 00000 00000 000000"""
    return 0xF0000000

# Register assignments
R1 = 1   # packet data
R2 = 2   # NIC status

# NIC addresses
NIC_IN_BUF    = 0xC000
NIC_IN_STATUS = 0xC001
NIC_OUT_BUF   = 0xC002
NIC_OUT_STATUS= 0xC003

# ============================================================
# Generate IMEM
# ============================================================

def generate_imem():
    """
    Generate the instruction memory contents.
    Returns list of 32-bit instruction words.
    PC = instruction index (word address).
    Branch targets are word addresses.
    """
    instructions = []

    for i in range(15):
        # Send packet i
        poll_s_pc = len(instructions)
        instructions.append(vld(R2, NIC_OUT_STATUS))   # poll output status
        instructions.append(vbnez(R2, poll_s_pc))       # loop if busy
        instructions.append(vld(R1, i))                 # load packet i
        instructions.append(vsd(R1, NIC_OUT_BUF))       # send to NIC

        # Receive packet i
        poll_r_pc = len(instructions)
        instructions.append(vld(R2, NIC_IN_STATUS))     # poll input status
        instructions.append(vbez(R2, poll_r_pc))        # loop if empty
        instructions.append(vld(R1, NIC_IN_BUF))        # read from NIC
        instructions.append(vsd(R1, 16 + i))            # store to MEM[16+i]

    # End NOPs
    for _ in range(4):
        instructions.append(vnop())

    return instructions

# ============================================================
# Packet construction
# ============================================================

def unary_hop(n):
    """Convert hop count n to 4-bit unary encoding."""
    if n == 0:
        return 0b0000
    return (1 << n) - 1

def build_packet(src_row, src_col, dst_row, dst_col):
    """
    Build a 64-bit packet using torus shortest-path XY routing.
    Route X (col) first, then Y (row).

    dirX: 1=East (dst_col increases), 0=West (dst_col decreases via wrap)
    dirY: 1=North (dst_row decreases via wrap), 0=South (dst_row increases)
    hopX: unary encoding of min(dist_east, dist_west)
    hopY: unary encoding of min(dist_south, dist_north)
    sourceX: src_col (8-bit)
    sourceY: src_row (8-bit)
    payload: upper 8 bits = source node id, lower 8 bits = dest node id
    """
    vc = 0

    dist_east  = (dst_col - src_col) % 4
    dist_west  = (src_col - dst_col) % 4
    dirX = 1 if dist_east <= dist_west else 0
    hopX = unary_hop(min(dist_east, dist_west))

    dist_south = (dst_row - src_row) % 4
    dist_north = (src_row - dst_row) % 4
    dirY = 0 if dist_south <= dist_north else 1
    hopY = unary_hop(min(dist_south, dist_north))

    sourceX = src_col & 0xFF
    sourceY = src_row & 0xFF

    src_id = src_row * 4 + src_col
    dst_id = dst_row * 4 + dst_col
    payload = ((src_id & 0xFF) << 8) | (dst_id & 0xFF)

    header = 0
    header |= (vc     & 0x1) << 31
    header |= (dirX   & 0x1) << 30
    header |= (dirY   & 0x1) << 29
    header |= (hopX   & 0xF) << 20
    header |= (hopY   & 0xF) << 16
    header |= (sourceX & 0xFF) << 8
    header |= (sourceY & 0xFF) << 0

    packet = (header << 32) | (payload & 0xFFFFFFFF)
    return packet

# ============================================================
# Generate DMEM per node
# ============================================================

def generate_dmem(src_row, src_col):
    """
    Generate dmem contents for node at (src_row, src_col).
    MEM[0..14]  = 15 outgoing packets (all destinations except self)
    MEM[15]     = 0 (sentinel)
    MEM[16..30] = 0 (receive slots, filled during simulation)
    MEM[31]     = 0
    """
    mem = [0] * 32  # 32 locations, all zero

    # Generate packets to all 15 other nodes
    # Order: row by row, col by col, skipping self
    dst_list = []
    for r in range(4):
        for c in range(4):
            if r == src_row and c == src_col:
                continue
            dst_list.append((r, c))

    # Should be exactly 15 destinations
    assert len(dst_list) == 15, f"Expected 15 destinations, got {len(dst_list)}"

    for i, (dst_row, dst_col) in enumerate(dst_list):
        mem[i] = build_packet(src_row, src_col, dst_row, dst_col)

    # MEM[15] = sentinel (already 0)
    # MEM[16..30] = receive slots (already 0)
    # MEM[31] = 0

    return mem

# ============================================================
# File writing helpers
# ============================================================

def write_imem(filename, instructions):
    """Write imem fill file."""
    with open(filename, 'w') as f:
        for instr in instructions:
            f.write(f"{instr:08X}\n")
    print(f"Written: {filename} ({len(instructions)} instructions)")

def write_dmem(filename, mem):
    """Write dmem fill file."""
    with open(filename, 'w') as f:
        for word in mem:
            f.write(f"{word:016X}\n")
    print(f"Written: {filename}")

# ============================================================
# Node naming: (row, col) -> "RC" string
# ============================================================

def node_name(row, col):
    return f"{row}{col}"

# ============================================================
# Main
# ============================================================

def main():
    os.makedirs("testcase_torus", exist_ok=True)

    # Generate imem (identical for all 16 nodes)
    instructions = generate_imem()
    print(f"\nIMEM: {len(instructions)} instructions")
    print(f"  Send phase: PC 0-{15*4-1}")
    print(f"  Recv phase: PC {15*4}-{15*4+15*4-1}")
    print(f"  End NOPs:   PC {15*4+15*4}-{15*4+15*4+3}")

    for row in range(4):
        for col in range(4):
            nn = node_name(row, col)
            fname = f"testcase_torus/cmp_test.imem.{nn}.fill"
            write_imem(fname, instructions)

    print()

    # Generate dmem (unique per node)
    for row in range(4):
        for col in range(4):
            nn = node_name(row, col)
            mem = generate_dmem(row, col)
            fname = f"testcase_torus/cmp_test.dmem.{nn}.fill"
            write_dmem(fname, mem)

            # Print packet table for this node
            print(f"\nNode {nn} (row={row}, col={col}) outgoing packets:")
            dst_list = [(r,c) for r in range(4) for c in range(4)
                        if not (r==row and c==col)]
            for i, (dr, dc) in enumerate(dst_list):
                pkt = mem[i]
                vc   = (pkt >> 63) & 0x1
                dirX = (pkt >> 62) & 0x1
                dirY = (pkt >> 61) & 0x1
                hopX = (pkt >> 52) & 0xF
                hopY = (pkt >> 48) & 0xF
                sX   = (pkt >> 40) & 0xFF
                sY   = (pkt >> 32) & 0xFF
                print(f"  MEM[{i:2d}] -> node{dr}{dc}: "
                      f"vc={vc} dirX={dirX}({'E' if dirX else 'W'}) "
                      f"dirY={dirY}({'N' if dirY else 'S'}) "
                      f"hopX={hopX:#06b} hopY={hopY:#06b} "
                      f"src=({sX},{sY}) | {pkt:016X}")
    
    # ============================================================
    # All-to-all hop count summary
    # ============================================================
    total_torus_hops = 0
    total_mesh_hops  = 0

    for sr in range(4):
        for sc in range(4):
            for dr in range(4):
                for dc in range(4):
                    if sr == dr and sc == dc:
                        continue
                    hx_torus = min((dc-sc)%4, (sc-dc)%4)
                    hy_torus = min((dr-sr)%4, (sr-dr)%4)
                    total_torus_hops += hx_torus + hy_torus
                    total_mesh_hops  += abs(dc-sc) + abs(dr-sr)

    print(f"\n============================================================")
    print(f"ALL-TO-ALL HOP COUNT SUMMARY (240 packets)")
    print(f"============================================================")
    print(f"  Mesh  total: {total_mesh_hops},  avg: {total_mesh_hops/240:.2f} hops")
    print(f"  Torus total: {total_torus_hops}, avg: {total_torus_hops/240:.2f} hops")
    print(f"  Reduction:   {(total_mesh_hops-total_torus_hops)*100/total_mesh_hops:.1f}%")
    print(f"============================================================")

    print("\nDone! All files written to testcase_torus/")

if __name__ == "__main__":
    main()