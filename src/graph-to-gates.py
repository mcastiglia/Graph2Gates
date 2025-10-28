#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import math
import random
import numpy as np
import argparse
import copy
import time
import os
import hashlib
import subprocess
import shutil
import sys
import global_vars
from init_graphs import get_normal_init, get_brent_kung_init, get_sklansky_init
from node_class import Node
args = None
result_cache = {}
cache_hit = 0

def parse_arguments():
    global args, INPUT_BIT, flog
    
    parser = argparse.ArgumentParser(description='Prefix graph to adder netlist conversion tool')
    parser.add_argument('-n','--input_bitwidth', type = int, required=True)
    parser.add_argument('--adder_type', type = int, required=True)
    parser.add_argument('--step_count', type = int, default = 1666)
    parser.add_argument('--openroad_path', type = str, default = 'OpenROAD/prefix-flow/')
    # parser.add_argument('--save_verilog', action = 'store_true', default = False)
    parser.add_argument('--synth', action = 'store_true', default = False)
    parser.add_argument('--output_dir', type = str, default = 'out/',
                       help='Output directory for generated files')
    parser.add_argument('--mode', type = str, choices=['generate', 'train'], default='generate',
                       help='Mode: generate initial Verilog or run training')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("ARGUMENT CONFIGURATION")
    print("=" * 50)
    print(f"Input bitwidth: {args.input_bitwidth}")
    print(f"Adder type: {args.adder_type}")
    print(f"Step limit: {args.step_count}")
    print(f"OpenROAD path: {args.openroad_path}")
    # print(f"Save verilog: {args.save_verilog}")
    print(f"Synthesize design: {args.synth}")
    print(f"Output directory: {args.output_dir}")
    print(f"Mode: {args.mode}")
    print("=" * 50)

    global_vars.initial_adder_type = args.adder_type
    INPUT_BIT = args.input_bitwidth
    strftime = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    
    # Create output directory structure
    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)
    if not os.path.exists(os.path.join(args.output_dir, "adder_parc_log")):
        os.mkdir(os.path.join(args.output_dir, "adder_parc_log"))
    if not os.path.exists(os.path.join(args.output_dir, "adder_parc_log/adder_{}b".format(INPUT_BIT))):
        os.mkdir(os.path.join(args.output_dir, "adder_parc_log/adder_{}b".format(INPUT_BIT)))
    global_vars.flog = open(os.path.join(args.output_dir, "adder_parc_log/adder_{}b/adder_{}b_openroad_type{}_{}.log".format(INPUT_BIT, 
        INPUT_BIT, args.adder_type, strftime)), "w")

    global_vars.start_time = time.time()
    
    return args


def tree_policy(node: Node) -> Node:
    eps = 0.8
    while node.get_state().is_terminal() == False:
        if node.is_all_expand() or (random.random() > eps and len(node.get_children()) >= 1):
            print("IS ALL EXPAND")
            node = best_child(node, True)
        else:
            node = expand(node)
            break
    return node


def default_policy(node: Node) -> float:
    current_state = node.get_state()
    best_state_reward = current_state.compute_reward()
    step = 0
    while current_state.is_terminal() == False and \
        ((step < 16 and global_vars.initial_adder_type == 0) or
            (step < 16 and global_vars.initial_adder_type != 0)):
        current_state = current_state.get_next_state_with_random_choice(args.step_count, args.output_dir, args.synth, args.openroad_path)
        if current_state is None:
            break 
        print("step = {}".format(step))
        step += 1
        best_state_reward = max(best_state_reward, current_state.compute_reward())
    print("default policy finished")
    return best_state_reward


def expand(node: Node) -> Node:
    tried_sub_node_states = [
        sub_node.get_state().action for sub_node in node.get_children()
    ]
    new_state = node.get_state().get_next_state_with_random_choice(args.step_count, args.output_dir, args.synth, args.openroad_path)
    while new_state.action in tried_sub_node_states:
        new_state = node.get_state().get_next_state_with_random_choice(args.step_count, args.output_dir, args.synth, args.openroad_path)

    sub_node = Node()
    sub_node.set_state(new_state)
    node.add_child(sub_node)
    return sub_node


def best_child(node: Node, is_exploration: bool) -> Node:
    best_score = -sys.maxsize
    best_sub_node = None
    for sub_node in node.get_children():
        if is_exploration:
            C = 1 / math.sqrt(2.0)
        else:
            C = 0.0

        if node.get_visit_times() >= 1e-2 and sub_node.get_visit_times() >= 1e-2:
            left = sub_node.get_best_reward() * 0.99 + sub_node.get_quality_value() / sub_node.get_visit_times() * 0.01 
            right = math.log(node.get_visit_times()) / sub_node.get_visit_times()
            right = C * 10 *  math.sqrt(right)
            print("left = {}, right = {}".format(left, right))
            score = left + right
        else:
            score = 1e9

        if score > best_score:
            best_sub_node = sub_node
            best_score = score

    return best_sub_node


def backup(node: Node, reward: float) -> Node:
    while node != None:

        node.visit_times_add_one()
        node.quality_value_add_n(reward)
        node.update_best_reward(reward)

        if node.parent is not None:
            node = node.parent
        else:
            break
    
    assert node is not None
    assert node.parent is None
    return node


def monte_carlo_tree_search(node: Node) -> None:
    computation_budget = int(1e6)

    for i in range(computation_budget):

        node = tree_policy(node)
        reward = default_policy(node)
        node = backup(node, reward)

        assert node.parent is None


def get_min_map_from_cell_map(cell_map):
    min_map = copy.deepcopy(cell_map)
    for i in range(INPUT_BIT):
        min_map[i, i] = 0
        min_map[i, 0] = 0
    return min_map


def search_best_adder(n: int):
    if global_vars.initial_adder_type == 0:
        init_state = get_normal_init(n)
    elif global_vars.initial_adder_type == 1:
        init_state = get_sklansky_init(n)
    else:
        init_state = get_brent_kung_init(n)
    init_state.output_verilog(args.output_dir)
    init_state.run_yosys(args.output_dir, args.openroad_path, args.synth)
    delay, area, power = init_state.run_openroad(args.output_dir, args.openroad_path)
    print("delay = {}, area = {}".format(delay, area))
    init_node = Node()
    init_node.set_state(init_state)
    current_node = init_node
    monte_carlo_tree_search(current_node)


def recover_cell_map_from_cell_map_str(cell_map_str):
    assert len(cell_map_str) == INPUT_BIT ** 2
    cell_map = np.zeros((INPUT_BIT, INPUT_BIT))
    for i in range(INPUT_BIT):
        for j in range(INPUT_BIT):
            cell_map[i, j] = int(cell_map_str[i * INPUT_BIT + j])
    return cell_map

def output_cell_map(input_bitwidth, max_levels, cell_map, hash_value, output_dir):
        verilog_mid_dir = os.path.join(output_dir, "run_verilog_mid")
        if not os.path.exists(verilog_mid_dir):
            os.mkdir(verilog_mid_dir)
        fdot_save = open(os.path.join(verilog_mid_dir, "adder_{}b_{}_{}_{}.log".format(input_bitwidth, 
                int(max_levels), int(cell_map.sum()-input_bitwidth),
                hash_value)), 'w')
        for i in range(input_bitwidth):
            for j in range(input_bitwidth):
                fdot_save.write("{}".format(str(int(cell_map[i, j]))))
            fdot_save.write("\n")
        fdot_save.write("\n")
        fdot_save.close()

def get_represent_int(input_bitwidth, cell_map):
    rep_int = 0
    for i in range(1, input_bitwidth):
        for j in range(i):
            if cell_map[i,j] == 1:
                rep_int = rep_int * 2 + 1
            else:
                rep_int *= 2
    return rep_int
    
def output_verilog(input_bitwidth, max_levels, cell_map, hash_value, output_dir, file_name = None):
        verilog_mid_dir = os.path.join(output_dir, "run_verilog_mid")
        if not os.path.exists(verilog_mid_dir):
            os.mkdir(verilog_mid_dir)
            
        # Create a unique hash identifier for each adder state
        rep_int = get_represent_int(input_bitwidth, cell_map)
        hash_value = hashlib.md5(str(rep_int).encode()).hexdigest()
        output_cell_map(input_bitwidth, max_levels, cell_map, hash_value, output_dir)
        if file_name is None:
            file_name = os.path.join(verilog_mid_dir, "adder_{}b_{}_{}_{}.v".format(input_bitwidth, 
                int(max_levels), int(cell_map.sum()-input_bitwidth),
                hash_value))
        verilog_file_name = file_name.split("/")[-1]

        verilog_file = open(file_name, "w")
        verilog_file.write("module adder_top(\n")
        verilog_file.write("\tinput [{}:0] a,b,\n".format(input_bitwidth-1))
        verilog_file.write("\toutput [{}:0] s,\n".format(input_bitwidth-1))
        verilog_file.write("\toutput cout\n")
        verilog_file.write(");\n\n")
        wires = set()
        for i in range(input_bitwidth):
            wires.add("c{}".format(i))
        
        for x in range(input_bitwidth-1, 0, -1):
            last_y = x
            for y in range(x-1, -1, -1):
                if cell_map[x, y] == 1:
                    assert cell_map[last_y-1, y] == 1
                    if y==0:
                        wires.add("g{}_{}".format(x, last_y))
                        wires.add("p{}_{}".format(x, last_y))
                        wires.add("g{}_{}".format(last_y-1, y))
                    else:
                        wires.add("g{}_{}".format(x, last_y))
                        wires.add("p{}_{}".format(x, last_y))
                        wires.add("g{}_{}".format(last_y-1, y))
                        wires.add("p{}_{}".format(last_y-1, y))
                        wires.add("g{}_{}".format(x, y))
                        wires.add("p{}_{}".format(x, y))
                    last_y = y
        
        for i in range(input_bitwidth):
            wires.add("p{}_{}".format(i, i))
            wires.add("g{}_{}".format(i, i))
            wires.add("c{}".format(x))
        assert 0 not in wires
        assert "0" not in wires
        verilog_file.write("wire ")
        
        for i, wire in enumerate(wires):
            if i < len(wires) - 1:
                    verilog_file.write("{},".format(wire))
            else:
                verilog_file.write("{};\n".format(wire))
        verilog_file.write("\n")
        
        for i in range(input_bitwidth):
            verilog_file.write('assign p{}_{} = a[{}] ^ b[{}];\n'.format(i,i,i,i))
            verilog_file.write('assign g{}_{} = a[{}] & b[{}];\n'.format(i,i,i,i))
        
        for i in range(1, input_bitwidth):
            verilog_file.write('assign g{}_0 = c{};\n'.format(i, i))
        
        for x in range(input_bitwidth-1, 0, -1):
            last_y = x
            for y in range(x-1, -1, -1):
                if cell_map[x, y] == 1:
                    assert cell_map[last_y-1, y] == 1
                    if y == 0: # add grey module
                        verilog_file.write('GREY grey{}(g{}_{}, p{}_{}, g{}_{}, c{});\n'.format(
                            x, x, last_y, x, last_y, last_y-1, y, x
                        ))
                    else:
                        verilog_file.write('BLACK black{}_{}(g{}_{}, p{}_{}, g{}_{}, p{}_{}, g{}_{}, p{}_{});\n'.format(
                            x, y, x, last_y, x, last_y, last_y-1, y, last_y-1, y, x, y, x, y 
                        ))
                    last_y = y
        
        verilog_file.write('assign s[0] = a[0] ^ b[0];\n')
        verilog_file.write('assign c0 = g0_0;\n')
        verilog_file.write('assign cout = c{};\n'.format(input_bitwidth-1))
        for i in range(1, self.input_bit):
            verilog_file.write('assign s[{}] = p{}_{} ^ c{};\n'.format(i, i, i, i-1))
        verilog_file.write("endmodule")
        verilog_file.write("\n\n")

        verilog_file.write(global_vars.GREY_CELL)
        verilog_file.write("\n")
        verilog_file.write(global_vars.BLACK_CELL)
        verilog_file.write("\n")
        verilog_file.close()

    # Create and run yosys script to map current adder state to a technology library
    def run_yosys(verilog_file_name, output_dir, openroad_path, synth):
        yosys_mid_dir = os.path.join(output_dir, "run_yosys_mid")
        if not os.path.exists(yosys_mid_dir):
            os.mkdir(yosys_mid_dir)
        dst_file_name = os.path.join(yosys_mid_dir, verilog_file_name.split(".")[0] + "_yosys.v")
        file_name_prefix = verilog_file_name.split(".")[0] + "_yosys"
        if os.path.exists(dst_file_name):
            return
        src_file_path = os.path.join(output_dir, "run_verilog_mid", verilog_file_name)

        yosys_script_dir = os.path.join(output_dir, "run_yosys_script")
        if not os.path.exists(yosys_script_dir):
            os.mkdir(yosys_script_dir)
        yosys_script_file_name = os.path.join(yosys_script_dir, 
            "{}.ys".format(file_name_prefix))
        fopen = open(yosys_script_file_name, "w")
        fopen.write(global_vars.yosys_script_format.format(src_file_path, openroad_path, dst_file_name))
        fopen.close()
        _ = subprocess.check_output(["yosys {}".format(yosys_script_file_name)], shell= True)
        # Keep source files for synthesis if synth flag is set
        if not synth:
            os.remove(src_file_path)
    
    def extract_results(report):
        lines = report.split("\n")[-15:]
        area = -100.0
        wslack = -100.0
        power = 0.0
        note = None
        for line in lines:
            if not line.startswith("result:") and not line.startswith("Total"):
                continue
            print("line", line)
            if "design_area" in line:
                area = float(line.split(" = ")[-1])
            elif "worst_slack" in line:
                wslack = float(line.split(" = ")[-1])
                note = lines
            elif "Total" in line:
                power = float(line.split()[-2])

        return area, wslack, power, note
    
    def run_openroad(verilog_file_name, output_dir, openroad_path):
        global result_cache
        global cache_hit

        file_name_prefix = verilog_file_name.split(".")[0]
        hash_idx = file_name_prefix.split("_")[-1]
        if hash_idx in result_cache:
            delay = result_cache[hash_idx]["delay"]
            area = result_cache[hash_idx]["area"]
            power = result_cache[hash_idx]["power"]
            cache_hit += 1
            delay = delay
            area = area
            power = power
            return delay, area, power
        
        verilog_file_path = "{}adder_tmp_{}.v".format(openroad_path, file_name_prefix)
        yosys_file_name = os.path.join(output_dir, "run_yosys_mid", verilog_file_name.split(".")[0] + "_yosys.v")
        shutil.copyfile(yosys_file_name, verilog_file_path)
        
        sdc_file_path = "{}adder_nangate45_{}.sdc".format(openroad_path, file_name_prefix)
        fopen_sdc = open(sdc_file_path, "w")
        fopen_sdc.write(global_vars.sdc_format)
        fopen_sdc.close()
        fopen_tcl = open("{}adder_nangate45_{}.tcl".format(openroad_path, file_name_prefix), "w")
        fopen_tcl.write(global_vars.openroad_tcl.format("adder_tmp_{}.v".format(file_name_prefix), 
            "adder_nangate45_{}.sdc".format(file_name_prefix)))
        fopen_tcl.close()
        
        # Ensure openroad_path ends with '/' for consistent path handling
        if not openroad_path.endswith('/'):
            openroad_path = openroad_path + '/'
            
        tcl_script = "adder_nangate45_{}.tcl".format(file_name_prefix)
        command = "openroad {}".format(tcl_script)
        # print("COMMAND: {}".format(command))
        print("Working directory: {}".format(openroad_path))
        
        output = subprocess.check_output(['openroad', tcl_script], 
            cwd=openroad_path).decode('utf-8')
        
        note = None
        retry = 0
        area, wslack, power, note = extract_results(output)
        while note is None and retry < 3:
            output = subprocess.check_output(['openroad', tcl_script], 
                cwd=openroad_path).decode('utf-8')
            area, wslack, power, note = substract_results(output)
            retry += 1
        if os.path.exists(yosys_file_name):
            os.remove(yosys_file_name)
        if os.path.exists("{}adder_nangate45_{}.tcl".format(openroad_path, 
                file_name_prefix)):
            os.remove("{}adder_nangate45_{}.tcl".format(openroad_path, file_name_prefix))
        if os.path.exists("{}/adder_nangate45_{}.sdc".format(openroad_path, 
                file_name_prefix)):
            os.remove("{}adder_nangate45_{}.sdc".format(openroad_path, file_name_prefix))
        if os.path.exists("{}/adder_tmp_{}.v".format(openroad_path, 
                file_name_prefix)):
            os.remove("{}adder_tmp_{}.v".format(openroad_path,file_name_prefix))
        delay = global_vars.CLOCK_PERIOD_TARGET - wslack
        delay *= 1000
        delay = delay
        area = area
        power = power
        
        # Cache PPA results for future states
        result_cache[hash_idx] = {"delay": delay, "area": area, "power": power}
        return delay, area, power
    
def generate_initial_verilog():
    """Generate Verilog file for the initial adder state without running training"""
    print("=" * 60)
    print("GENERATING INITIAL ADDER VERILOG")
    print("=" * 60)
    
    # Get initial state based on adder type
    if global_vars.initial_adder_type == 0:
        print("Using Normal (Linear) adder initialization")
        cell_map, min_map = get_normal_cell_map(args.input_bitwidth)
    elif global_vars.initial_adder_type == 1:
        print("Using Sklansky adder initialization")
        cell_map, min_map = get_sklansky_cell_map(args.input_bitwidth)
    else:
        print("Using Brent-Kung adder initialization")
        cell_map, min_map = get_brent_kung_cell_map(args.input_bitwidth)
    
    # Generate Verilog file
    print(f"Generating Verilog for {INPUT_BIT}-bit adder...")
    output_verilog(args.input_bitwidth, max_levels, cell_map, hash_value, args.output_dir)
    print(f"Verilog file generated: {init_state.verilog_file_name}")
    
    # Optional: Run synthesis and analysis
    if args.synth:
        print("Running Yosys synthesis...")
        init_state.run_yosys(args.output_dir, args.openroad_path, args.synth)
        print("Running OpenROAD synthesis...")
        delay, area, power = init_state.run_openroad(args.output_dir, args.openroad_path)
        print(f"Performance metrics - Delay: {delay:.2f}, Area: {area:.2f}, Power: {power:.2f}")
    
    print("=" * 60)
    print("INITIAL ADDER GENERATION COMPLETE")
    print("=" * 60)
    
    return init_state

def main():
    global args
    args = parse_arguments()
    
    # Generate Verilog file
    if args.mode == 'generate':
        generate_initial_verilog()
    elif args.mode == 'train':
        print("=" * 60)
        print("STARTING MONTE CARLO TREE SEARCH TRAINING")
        print("=" * 60)
        search_best_adder(args.input_bitwidth)


if __name__ == "__main__":
    main()