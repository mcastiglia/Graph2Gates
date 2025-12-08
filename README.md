# Graph-to-Gates: Optimization of Parallel Prefix Circuits using Reinforcement Learning
## EEL 6938 Group Project

```
   _____                 _       _           _____       _             
  / ____|               | |     | |         / ____|     | |            
 | |  __ _ __ __ _ _ __ | |__   | |_ ___   | |  __  __ _| |_ ___  ___  
 | | |_ | '__/ _` | '_ \| '_ \  | __/ _ \  | | |_ |/ _` | __/ _ \/ __| 
 | |__| | | | (_| | |_) | | | | | || (_) | | |__| | (_| | ||  __/\__ \ 
  \_____|_|  \__,_| .__/|_| |_|  \__\___/   \_____|\__,_|\__\___||___/ 
                  | |                                                  
                  |_|                                                  
```

### Group
- Cory Brynds, MS CpE
- John Gierlach, MS CpE
- Michael Castiglia, MS CpE
- Francisco Soriano, MS CpE

### Overview
Graph-to-Gates (G2G) is an implementation of *PrefixRL: Optimization of Parallel Prefix Circuits using Deep
Reinforcement Learning*, a DAC 2021 paper exploring the use of RL in the optimization of parallel prefix circuits, which are a fundamental component in high-performance binary adders, binary-to-grey code converters, leading zero counters, and other ASIC circuits. 

G2G adapts auxillary functions and implementation flows from ArithTree RL, a GitHub repository associated with the NeurIPS 2024 paper *Scalable and Effective Arithmetic Tree Generation for Adder and Multiplier Designs*.

`graph-to-gates-final.pdf` details the technical implementation of the project and served as our final project report in EEL6938. It also contains the results we were able to achieve against commercial tool-generated adders.

`EEL-6978-G2G-Presentation.pdf` is a PDF of the PowerPoint slides from our final course presentation. It contains additional background information and graphics related to the project.

### Repository Structure
```
├── EEL6978-G2G-Presentation.pdf          # Final project presentation slides
├── graph-to-gates-final.pdf              # Technical report and results
├── README.md                             # This file
├── docker/                               # Docker configurations for different platforms
│   ├── cuda/
│   │   └── dockerfile                    # CUDA-based Docker setup
│   └── rocm/
│       └── dockerfile                    # ROCm-based Docker setup
├── OpenROAD/                             # OpenROAD ASIC flow setup
│   ├── openroad.def                      # OpenROAD apptainer definitions file
│   ├── README.md                         # OpenROAD-specific documentation
│   └── prefix-flow/                      # OpenROAD flow scripts and libraries
│       ├── adder_nangate45_adder_32b.sdc # SDC constraints
│       ├── fast_flow.tcl                 # Fast synthesis flow
│       ├── flow_helpers.tcl              # Helper scripts
│       ├── full_flow.tcl                 # Full synthesis flow
│       ├── helpers.tcl                   # Utility scripts
│       ├── NangateOpenCellLibrary_typical.lib # Standard cell library
│       ├── openroad_flow.tcl             # Main OpenROAD flow
│       ├── README.md                     # Flow documentation
│       ├── yosys_flow.tcl                # Yosys integration
│       └── Nangate45/                    # Nangate 45nm PDK files
├── prefixrl-cnn/                         # Main source code of the project
│   ├── environment.py                    # RL environment for adder optimization
│   ├── global_vars.py                    # Global configuration variables
│   ├── graph_to_gates.py                 # Main training script with command-line arguments
│   ├── init_states.py                    # Initial state generation
│   ├── plotting_utils.py                 # Visualization utilities
│   ├── q_network.py                      # Q-network and training logic
│   ├── training_timer.py                 # Training timing utilities
│   └── analysis/                         # Analysis and evaluation scripts
├── resources/                            # Research papers and references
│   ├── prefixrl.pdf                      # Original PrefixRL paper
│   ├── adders/                           # Adder-related papers
│   │   ├── A_taxonomy_of_parallel_prefix_networks.pdf
│   │   ├── fixed-point-addition.pdf
│   │   ├── Parallel prefix adders presentation.pdf
│   │   └── zimmermann-adder-arch-synthesis.pdf
│   └── power-optimizations/               # Power optimization papers
│       └── Robust_Energy-Efficient_Adder_Topologies.pdf
├── rtla-synthesis/                       # RTL synthesis tools
```

### Usage
To run Graph-to-Gates training, use the `graph_to_gates.py` script in the `prefixrl-cnn/` directory. The script supports various command-line options for configuring the RL training process.

#### Basic Command
```bash
cd prefixrl-cnn
python3 graph_to_gates.py -n <bitwidth> [options]
```

#### Command-Line Options
| Option | Description | Default |
|--------|-------------|---------|
| `-n, --input_bitwidth` | Input bitwidth for the adder (required) | - |
| `--adder_type` | Initial starting state for prefix graph (0: serial, 1: sklansky, 2: brent-kung) | 0 |
| `--use_analytic_model` | Use analytic model for delay and area | False |
| `-b, --batch_size` | Batch size for RL training | 192 |
| `--num_steps` | Number of training steps per episode | 5000 |
| `--num_episodes` | Number of training episodes | 100 |
| `--w_scalar` | Weight scalar for area and delay (w_area = w_scalar, w_delay = 1 - w_scalar) | 0.5 |
| `--openroad_path` | Path to OpenROAD flow directory | `../OpenROAD/prefix-flow/` |
| `--flow_type` | Flow type for OpenROAD (fast_flow or full_flow) | `fast_flow` |
| `--output_dir` | Output directory for generated files | `out/` |
| `--save_verilog` | Save the generated Verilog files | False |
| `--disable_parallel_evaluation` | Disable parallel synthesis and PnR for next state evaluation | False |
| `--restore_from` | Path to checkpoint file to restore from | None |
| `--disable_checkpointing` | Disable checkpointing during training | False |
