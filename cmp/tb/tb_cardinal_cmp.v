/// tb_cardinal_cpu.v ///

`timescale 1ns/1ps

module tb_cardinal_cmp;


    parameter CYCLE_TIME = 4;     // 4 ns period = 250 MHz
    parameter MAX_CYCLES = 5000;   // increase if your program is long

    reg clk;
    reg reset;

    cardinal_cmp dut (
        .clk   (clk),
        .reset (reset)
    );

    // Snoop log

    integer snoop_fd;

    always #(CYCLE_TIME/2) clk = ~clk;

    // ============================================================
    // Snoop helper tasks
    // ============================================================
    task log_send;
        input integer node_id;
        input [0:63] data;
    begin
        $fdisplay(snoop_fd,
                  "[%0t] NODE%0d NIC->ROUTER  data=%h",
                  $time, node_id, data);
    end
    endtask

    task log_recv;
        input integer node_id;
        input [0:63] data;
    begin
        $fdisplay(snoop_fd,
                  "[%0t] NODE%0d ROUTER->NIC  data=%h",
                  $time, node_id, data);
    end
    endtask

    // Optional utility: dump memory
    task dump_all_dmems;
    begin
        $writememh("cmp_test.dmem.00.dump", dut.node00.dmem.MEM);
        $writememh("cmp_test.dmem.01.dump", dut.node01.dmem.MEM);
        $writememh("cmp_test.dmem.02.dump", dut.node02.dmem.MEM);
        $writememh("cmp_test.dmem.03.dump", dut.node03.dmem.MEM);

        $writememh("cmp_test.dmem.10.dump", dut.node10.dmem.MEM);
        $writememh("cmp_test.dmem.11.dump", dut.node11.dmem.MEM);
        $writememh("cmp_test.dmem.12.dump", dut.node12.dmem.MEM);
        $writememh("cmp_test.dmem.13.dump", dut.node13.dmem.MEM);

        $writememh("cmp_test.dmem.20.dump", dut.node20.dmem.MEM);
        $writememh("cmp_test.dmem.21.dump", dut.node21.dmem.MEM);
        $writememh("cmp_test.dmem.22.dump", dut.node22.dmem.MEM);
        $writememh("cmp_test.dmem.23.dump", dut.node23.dmem.MEM);

        $writememh("cmp_test.dmem.30.dump", dut.node30.dmem.MEM);
        $writememh("cmp_test.dmem.31.dump", dut.node31.dmem.MEM);
        $writememh("cmp_test.dmem.32.dump", dut.node32.dmem.MEM);
        $writememh("cmp_test.dmem.33.dump", dut.node33.dmem.MEM);
    end
    endtask

    // ============================================================
    // Memory preload
    // ============================================================
    task load_all_memories;
    begin
        // -----------------------------
        // Row 0
        // -----------------------------
        $readmemh("cmp_test.imem.00.fill", dut.node00.imem.MEM);
        $readmemh("cmp_test.dmem.00.fill", dut.node00.dmem.MEM);

        $readmemh("cmp_test.imem.01.fill", dut.node01.imem.MEM);
        $readmemh("cmp_test.dmem.01.fill", dut.node01.dmem.MEM);

        $readmemh("cmp_test.imem.02.fill", dut.node02.imem.MEM);
        $readmemh("cmp_test.dmem.02.fill", dut.node02.dmem.MEM);

        $readmemh("cmp_test.imem.03.fill", dut.node03.imem.MEM);
        $readmemh("cmp_test.dmem.03.fill", dut.node03.dmem.MEM);

        // -----------------------------
        // Row 1
        // -----------------------------
        $readmemh("cmp_test.imem.10.fill", dut.node10.imem.MEM);
        $readmemh("cmp_test.dmem.10.fill", dut.node10.dmem.MEM);

        $readmemh("cmp_test.imem.11.fill", dut.node11.imem.MEM);
        $readmemh("cmp_test.dmem.11.fill", dut.node11.dmem.MEM);

        $readmemh("cmp_test.imem.12.fill", dut.node12.imem.MEM);
        $readmemh("cmp_test.dmem.12.fill", dut.node12.dmem.MEM);

        $readmemh("cmp_test.imem.13.fill", dut.node13.imem.MEM);
        $readmemh("cmp_test.dmem.13.fill", dut.node13.dmem.MEM);

        // -----------------------------
        // Row 2
        // -----------------------------
        $readmemh("cmp_test.imem.20.fill", dut.node20.imem.MEM);
        $readmemh("cmp_test.dmem.20.fill", dut.node20.dmem.MEM);

        $readmemh("cmp_test.imem.21.fill", dut.node21.imem.MEM);
        $readmemh("cmp_test.dmem.21.fill", dut.node21.dmem.MEM);

        $readmemh("cmp_test.imem.22.fill", dut.node22.imem.MEM);
        $readmemh("cmp_test.dmem.22.fill", dut.node22.dmem.MEM);

        $readmemh("cmp_test.imem.23.fill", dut.node23.imem.MEM);
        $readmemh("cmp_test.dmem.23.fill", dut.node23.dmem.MEM);

        // -----------------------------
        // Row 3
        // -----------------------------
        $readmemh("cmp_test.imem.30.fill", dut.node30.imem.MEM);
        $readmemh("cmp_test.dmem.30.fill", dut.node30.dmem.MEM);

        $readmemh("cmp_test.imem.31.fill", dut.node31.imem.MEM);
        $readmemh("cmp_test.dmem.31.fill", dut.node31.dmem.MEM);

        $readmemh("cmp_test.imem.32.fill", dut.node32.imem.MEM);
        $readmemh("cmp_test.dmem.32.fill", dut.node32.dmem.MEM);

        $readmemh("cmp_test.imem.33.fill", dut.node33.imem.MEM);
        $readmemh("cmp_test.dmem.33.fill", dut.node33.dmem.MEM);
    end
    endtask

    // ============================================================
    // Snoop monitors
    // - NIC -> Router: net_so && net_ro
    // - Router -> NIC: net_si && net_ri
    // ============================================================
    always @(posedge clk) begin
        if (!reset) begin
            if (dut.node00.nic.net_so && dut.node00.nic.net_ro)
                log_send(0, dut.node00.nic.net_do);
            if (dut.node00.nic.net_si && dut.node00.nic.net_ri)
                log_recv(0, dut.node00.nic.net_di);

            if (dut.node01.nic.net_so && dut.node01.nic.net_ro)
                log_send(1, dut.node01.nic.net_do);
            if (dut.node01.nic.net_si && dut.node01.nic.net_ri)
                log_recv(1, dut.node01.nic.net_di);

            if (dut.node02.nic.net_so && dut.node02.nic.net_ro)
                log_send(2, dut.node02.nic.net_do);
            if (dut.node02.nic.net_si && dut.node02.nic.net_ri)
                log_recv(2, dut.node02.nic.net_di);

            if (dut.node03.nic.net_so && dut.node03.nic.net_ro)
                log_send(3, dut.node03.nic.net_do);
            if (dut.node03.nic.net_si && dut.node03.nic.net_ri)
                log_recv(3, dut.node03.nic.net_di);

            if (dut.node10.nic.net_so && dut.node10.nic.net_ro)
                log_send(10, dut.node10.nic.net_do);
            if (dut.node10.nic.net_si && dut.node10.nic.net_ri)
                log_recv(10, dut.node10.nic.net_di);

            if (dut.node11.nic.net_so && dut.node11.nic.net_ro)
                log_send(11, dut.node11.nic.net_do);
            if (dut.node11.nic.net_si && dut.node11.nic.net_ri)
                log_recv(11, dut.node11.nic.net_di);

            if (dut.node12.nic.net_so && dut.node12.nic.net_ro)
                log_send(12, dut.node12.nic.net_do);
            if (dut.node12.nic.net_si && dut.node12.nic.net_ri)
                log_recv(12, dut.node12.nic.net_di);

            if (dut.node13.nic.net_so && dut.node13.nic.net_ro)
                log_send(13, dut.node13.nic.net_do);
            if (dut.node13.nic.net_si && dut.node13.nic.net_ri)
                log_recv(13, dut.node13.nic.net_di);

            if (dut.node20.nic.net_so && dut.node20.nic.net_ro)
                log_send(20, dut.node20.nic.net_do);
            if (dut.node20.nic.net_si && dut.node20.nic.net_ri)
                log_recv(20, dut.node20.nic.net_di);

            if (dut.node21.nic.net_so && dut.node21.nic.net_ro)
                log_send(21, dut.node21.nic.net_do);
            if (dut.node21.nic.net_si && dut.node21.nic.net_ri)
                log_recv(21, dut.node21.nic.net_di);

            if (dut.node22.nic.net_so && dut.node22.nic.net_ro)
                log_send(22, dut.node22.nic.net_do);
            if (dut.node22.nic.net_si && dut.node22.nic.net_ri)
                log_recv(22, dut.node22.nic.net_di);

            if (dut.node23.nic.net_so && dut.node23.nic.net_ro)
                log_send(23, dut.node23.nic.net_do);
            if (dut.node23.nic.net_si && dut.node23.nic.net_ri)
                log_recv(23, dut.node23.nic.net_di);

            if (dut.node30.nic.net_so && dut.node30.nic.net_ro)
                log_send(30, dut.node30.nic.net_do);
            if (dut.node30.nic.net_si && dut.node30.nic.net_ri)
                log_recv(30, dut.node30.nic.net_di);

            if (dut.node31.nic.net_so && dut.node31.nic.net_ro)
                log_send(31, dut.node31.nic.net_do);
            if (dut.node31.nic.net_si && dut.node31.nic.net_ri)
                log_recv(31, dut.node31.nic.net_di);

            if (dut.node32.nic.net_so && dut.node32.nic.net_ro)
                log_send(32, dut.node32.nic.net_do);
            if (dut.node32.nic.net_si && dut.node32.nic.net_ri)
                log_recv(32, dut.node32.nic.net_di);

            if (dut.node33.nic.net_so && dut.node33.nic.net_ro)
                log_send(33, dut.node33.nic.net_do);
            if (dut.node33.nic.net_si && dut.node33.nic.net_ri)
                log_recv(33, dut.node33.nic.net_di);
        end
    end

    // ============================================================
    // Main test sequence
    // ============================================================
    initial begin
        clk   = 1'b0;
        reset = 1'b1;

        snoop_fd = $fopen("snoop.log", "w");
        if (snoop_fd == 0) begin
            $display("[TB][ERROR] Cannot open snoop.log");
            $stop;
        end

        $fdisplay(snoop_fd, "==== snoop log start ====");

        // Load all node memories
        load_all_memories();

        // Hold reset for a few cycles
        repeat (4) @(posedge clk);
        reset = 1'b0;

        // Let system run
        repeat (MAX_CYCLES) @(posedge clk);

        // Dump memory contents
        dump_all_dmems();

        $fdisplay(snoop_fd, "==== snoop log end ====");
        $fclose(snoop_fd);

        $display("[TB] Finished after %0d cycles.", MAX_CYCLES);
        $stop;
    end

endmodule
