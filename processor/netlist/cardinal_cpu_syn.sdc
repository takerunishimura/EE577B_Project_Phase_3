###################################################################

# Created by write_sdc on Tue Apr  7 22:53:48 2026

###################################################################
set sdc_version 2.2

set_units -time ns -resistance kOhm -capacitance pF -voltage V -current uA
create_clock [get_ports clk]  -period 4  -waveform {0 2}
