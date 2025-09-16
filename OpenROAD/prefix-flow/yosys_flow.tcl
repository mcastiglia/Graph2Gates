# set DESIGN_NAME "adder_32b.sv"
# set OUTPUT_NAME "adder_32b_netlist.v"

read -sv "adder_32b.v"
hierarchy -top main
flatten
proc; techmap; opt;
abc -fast -liberty NangateOpenCellLibrary_typical.lib
write_verilog "adder_32b_netlist.v"

