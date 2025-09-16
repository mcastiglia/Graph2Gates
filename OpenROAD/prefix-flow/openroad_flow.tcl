source "helpers.tcl"
source "flow_helpers.tcl"
source "Nangate45/Nangate45.vars"

set design "adder"
set top_module "main"
set synth_verilog "adder_32b_netlist.v"
set sdc_file "adder_nangate45_adder_32b.sdc"

set die_area {0 0 80 80}
set core_area {0 0 80 80}

source -echo "full_flow.tcl"
