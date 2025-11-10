# OpenROAD Apptainer Image Usage Instructions 

from `/OpenROAD/` change script permissions

`chmod +x scripts/*.sh`

build the image

`scripts/build_sif.sh --def openroad.def --out openroad.sif`

open a shell in the apptainer environment

`apptainer shell --bind "$PWD":/workspace ./openroad.sif`

