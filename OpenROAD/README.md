# OpenROAD Apptainer Image Usage Instructions 

from repo root change script permissions

`chmod +x scripts/*.sh`

build the image

`scripts/build_sif.sh --def openroad.def --out openroad.sif`

run OpenROAD (example)

`apptainer shell --bind "$PWD":/workspace ./openroad.sif`

`cd /workspace`

`openroad -exit your_script.tcl`

