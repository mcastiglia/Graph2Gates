export DESIGN_NICKNAME = %DESIGN_NICKNAME
export DESIGN_NAME = %DESIGN_NAME
export PLATFORM    = nangate45

export VERILOG_FILES    = $(sort $(wildcard ./designs/src/$(DESIGN_NICKNAME)/*.sv))
export SDC_FILE         = ./designs/$(PLATFORM)/$(DESIGN_NICKNAME)/constraint.sdc

export CORE_UTILIZATION = 40
export PLACE_DENSITY    = 0.60

export TNS_END_PERCENT  = 100

