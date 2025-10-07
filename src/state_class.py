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

result_cache = {}
# start_time = {}
update_time = {}
output_time = {}
global_step = 0
cache_hit = 0
record_num = 0

class State(object):

    def __init__(self, input_bitwidth, level, size, cell_map, level_map, min_map,
            step_num, action, reward, level_bound_delta):
        self.current_value = 0.0
        self.current_round_index = 0
        self.input_bit = input_bitwidth
        self.cumulative_choices = []
        self.level = level
        self.cell_map = cell_map
        self.level_map = level_map
        self.fanout_map = np.zeros((self.input_bit, self.input_bit), dtype = np.int8)
        self.min_map = min_map
        self.reward = reward
        self.size = size
        self.delay = None
        self.area = None
        self.level_bound_delta = level_bound_delta
        self.level_bound = int(math.log2(input_bitwidth) + 1 + level_bound_delta)
        assert self.cell_map.sum() - self.input_bit == self.size

        up_tri_mask = np.triu(np.ones((self.input_bit, self.input_bit), dtype = np.int8),
            k = 1)
        self.prob = np.ones((2, self.input_bit, self.input_bit), dtype = np.int8)
        self.prob[0] = np.where(self.cell_map >= 1.0, 0, self.prob[0])
        self.prob[0] = np.where(up_tri_mask >= 1.0, 0, self.prob[0])
        self.prob[1] = np.where(self.min_map <= 0.0, 0, self.prob[1])
        self.prob[1] = np.where(up_tri_mask >= 1.0, 0, self.prob[1])

        self.available_choice_list = []
        cnt = 0
        for i in range(input_bitwidth):
            for j in range(input_bitwidth):
                if self.prob[1, i, j] == 1:
                    self.available_choice_list.append(self.input_bit **2 +i* self.input_bit+j)
                    cnt += 1
        for i in range(input_bitwidth):
            for j in range(input_bitwidth):
                if self.prob[0, i, j] == 1:
                    self.available_choice_list.append(i* self.input_bit+j)
                    cnt += 1
        self.available_choice = cnt
        self.action = action
        self.step_num = step_num

    def get_represent_int(self):
        rep_int = 0
        for i in range(1, self.input_bit):
            for j in range(i):
                if self.cell_map[i,j] == 1:
                    rep_int = rep_int * 2 + 1
                else:
                    rep_int *= 2
        self.rep_int = rep_int
        return rep_int
    
    def output_cell_map(self, output_dir):
        verilog_mid_dir = os.path.join(output_dir, "run_verilog_mid")
        if not os.path.exists(verilog_mid_dir):
            os.mkdir(verilog_mid_dir)
        fdot_save = open(os.path.join(verilog_mid_dir, "adder_{}b_{}_{}_{}.log".format(self.input_bit, 
                int(self.level_map.max()), int(self.cell_map.sum()-self.input_bit),
                self.hash_value)), 'w')
        for i in range(self.input_bit):
            for j in range(self.input_bit):
                fdot_save.write("{}".format(str(int(self.cell_map[i, j]))))
            fdot_save.write("\n")
        fdot_save.write("\n")
        fdot_save.close()

    def output_verilog(self, output_dir, file_name = None):
        verilog_mid_dir = os.path.join(output_dir, "run_verilog_mid")
        if not os.path.exists(verilog_mid_dir):
            os.mkdir(verilog_mid_dir)
            
        # Create a unique hash identifier for each adder state
        rep_int = self.get_represent_int()
        self.hash_value = hashlib.md5(str(rep_int).encode()).hexdigest()
        self.output_cell_map(output_dir)
        if file_name is None:
            file_name = os.path.join(verilog_mid_dir, "adder_{}b_{}_{}_{}.v".format(self.input_bit, 
                int(self.level_map.max()), int(self.cell_map.sum()-self.input_bit),
                self.hash_value))
        self.verilog_file_name = file_name.split("/")[-1]

        verilog_file = open(file_name, "w")
        verilog_file.write("module adder_top(\n")
        verilog_file.write("\tinput [{}:0] a,b,\n".format(self.input_bit-1))
        verilog_file.write("\toutput [{}:0] s,\n".format(self.input_bit-1))
        verilog_file.write("\toutput cout\n")
        verilog_file.write(");\n\n")
        wires = set()
        for i in range(self.input_bit):
            wires.add("c{}".format(i))
        
        for x in range(self.input_bit-1, 0, -1):
            last_y = x
            for y in range(x-1, -1, -1):
                if self.cell_map[x, y] == 1:
                    assert self.cell_map[last_y-1, y] == 1
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
        
        for i in range(self.input_bit):
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
        
        for i in range(self.input_bit):
            verilog_file.write('assign p{}_{} = a[{}] ^ b[{}];\n'.format(i,i,i,i))
            verilog_file.write('assign g{}_{} = a[{}] & b[{}];\n'.format(i,i,i,i))
        
        for i in range(1, self.input_bit):
            verilog_file.write('assign g{}_0 = c{};\n'.format(i, i))
        
        for x in range(self.input_bit-1, 0, -1):
            last_y = x
            for y in range(x-1, -1, -1):
                if self.cell_map[x, y] == 1:
                    assert self.cell_map[last_y-1, y] == 1
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
        verilog_file.write('assign cout = c{};\n'.format(self.input_bit-1))
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
    def run_yosys(self, output_dir, openroad_path, synth):
        yosys_mid_dir = os.path.join(output_dir, "run_yosys_mid")
        if not os.path.exists(yosys_mid_dir):
            os.mkdir(yosys_mid_dir)
        dst_file_name = os.path.join(yosys_mid_dir, self.verilog_file_name.split(".")[0] + "_yosys.v")
        file_name_prefix = self.verilog_file_name.split(".")[0] + "_yosys"
        if os.path.exists(dst_file_name):
            return
        src_file_path = os.path.join(output_dir, "run_verilog_mid", self.verilog_file_name)

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
    
    def run_openroad(self, output_dir, openroad_path):
        global result_cache
        global cache_hit
        def substract_results(p):
            lines = p.split("\n")[-15:]
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

        file_name_prefix = self.verilog_file_name.split(".")[0]
        hash_idx = file_name_prefix.split("_")[-1]
        if hash_idx in result_cache:
            delay = result_cache[hash_idx]["delay"]
            area = result_cache[hash_idx]["area"]
            power = result_cache[hash_idx]["power"]
            cache_hit += 1
            self.delay = delay
            self.area = area
            self.power = power
            return delay, area, power
        verilog_file_path = "{}adder_tmp_{}.v".format(openroad_path, file_name_prefix)
        yosys_file_name = os.path.join(output_dir, "run_yosys_mid", self.verilog_file_name.split(".")[0] + "_yosys.v")
        shutil.copyfile(yosys_file_name, verilog_file_path)
        
        sdc_file_path = "{}adder_nangate45_{}.sdc".format(openroad_path, file_name_prefix)
        fopen_sdc = open(sdc_file_path, "w")
        fopen_sdc.write(global_vars.sdc_format)
        fopen_sdc.close()
        fopen_tcl = open("{}adder_nangate45_{}.tcl".format(openroad_path, file_name_prefix), "w")
        fopen_tcl.write(global_vars.openroad_tcl.format("adder_tmp_{}.v".format(file_name_prefix), 
            "adder_nangate45_{}.sdc".format(file_name_prefix)))
        fopen_tcl.close()
        
        command = "openroad {}adder_nangate45_{}.tcl".format(openroad_path, file_name_prefix)
        # print("COMMAND: {}".format(command))
        output = subprocess.check_output(['openroad',
            "{}adder_nangate45_{}.tcl".format(openroad_path, file_name_prefix)], 
            cwd="{}".format(openroad_path)).decode('utf-8')
        note = None
        retry = 0
        area, wslack, power, note = substract_results(output)
        while note is None and retry < 3:
            output = subprocess.check_output(['openroad',
                "{}adder_nangate45_{}.tcl".format(openroad_path, file_name_prefix)], 
                shell=True, cwd="{}".format(openroad_path)).decode('utf-8')
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
        self.delay = delay
        self.area = area
        self.power = power
        
        # Cache PPA results for future states
        result_cache[hash_idx] = {"delay": delay, "area": area, "power": power}
        return delay, area, power

    def update_available_choice(self):
        up_tri_mask = np.triu(np.ones((self.input_bit, self.input_bit), dtype = np.int8), 
            k = 1)
        self.prob = np.ones((2, self.input_bit, self.input_bit), dtype = np.int8)
        self.prob[0] = np.where(self.cell_map >= 1.0, 0, self.prob[0])
        self.prob[0] = np.where(up_tri_mask >= 1.0, 0, self.prob[0])
        self.prob[1] = np.where(self.min_map <= 0.0, 0, self.prob[1])
        self.prob[1] = np.where(up_tri_mask >= 1.0, 0, self.prob[1])

        self.available_choice_list = []
        cnt = 0

        for i in range(self.input_bit):
            for j in range(self.input_bit):
                if self.prob[1, i, j] == 1:
                    self.available_choice_list.append(self.input_bit **2 + i * self.input_bit+j)
                    cnt += 1
        self.available_choice = cnt

    def is_terminal(self):
        if self.available_choice == 0:
            return True
        return False

    def compute_reward(self):
        if global_vars.initial_adder_type == 0:
            return - (self.area) 
        else:
            return - (self.delay + self.area)

    def legalize(self, cell_map, min_map):
        min_map = copy.deepcopy(cell_map)
        for i in range(self.input_bit):
            min_map[i, 0] = 0
            min_map[i, i] = 0
        for x in range(self.input_bit-1, 0, -1):
            last_y = x
            for y in range(x-1, -1, -1):
                if cell_map[x, y] == 1:
                    cell_map[last_y-1, y] = 1
                    min_map[last_y-1, y] = 0
                    last_y = y
        return cell_map, min_map

    def update_fanout_map(self):
        self.fanout_map.fill(0)
        self.fanout_map[0, 0] = 0
        for x in range(1, self.input_bit):
            self.fanout_map[x, x] = 0
            last_y = x
            for y in range(x-1, -1, -1):
                if self.cell_map[x, y] == 1:
                    self.fanout_map[last_y-1, y] += 1
                    self.fanout_map[x, last_y] += 1
                    last_y = y

    def update_level_map(self, cell_map, level_map):
        level_map[1:].fill(0)
        level_map[0, 0] = 1
        for x in range(1, self.input_bit):
            level_map[x, x] = 1
            last_y = x
            for y in range(x-1, -1, -1):
                if cell_map[x, y] == 1:
                    level_map[x, y] = max(level_map[x, last_y], level_map[last_y-1, y])+ 1
                    last_y = y
        return level_map

    def get_next_state_with_random_choice(self, step_count, output_dir, synth, openroad_path):
        global global_step
        global record_num
        try_step = 0
        min_metric = 1e10
        while self.available_choice > 0 and \
            ((global_vars.initial_adder_type != 0 and try_step < 4) or \
            (global_vars.initial_adder_type == 0 and try_step < 4) ):
            sample_prob = np.ones((self.available_choice))
            choice_idx = np.random.choice(self.available_choice, size = 1, replace=False, 
                    p = sample_prob/sample_prob.sum())[0]
            random_choice = self.available_choice_list[choice_idx]
            action_type = random_choice // (self.input_bit ** 2)
            x = (random_choice % (self.input_bit ** 2)) // self.input_bit
            y = (random_choice % (self.input_bit ** 2)) % self.input_bit
            next_cell_map = copy.deepcopy(self.cell_map)
            next_min_map = np.zeros((self.input_bit, self.input_bit))
            next_level_map = np.zeros((self.input_bit, self.input_bit))

            if action_type == 0:
                assert next_cell_map[x, y] == 0
                next_cell_map[x, y] = 1
                next_cell_map, next_min_map = self.legalize(next_cell_map, next_min_map)
            elif action_type == 1:
                assert self.min_map[x, y] == 1
                assert self.cell_map[x, y] == 1
                next_cell_map[x, y] = 0
                next_cell_map, next_min_map = self.legalize(next_cell_map, next_min_map)
            next_level_map = self.update_level_map(next_cell_map, next_level_map)
            next_level = next_level_map.max()
            next_size = next_cell_map.sum() - self.input_bit
            next_step_num = self.step_num + 1
            action = random_choice
            reward = 0

            next_state = State(self.input_bit, next_level, next_size, next_cell_map,
                next_level_map, next_min_map, 
                next_step_num, action, reward, self.level_bound_delta)
            
            next_state.output_verilog(output_dir)
            next_state.run_yosys(output_dir, openroad_path, synth)
            delay, area, power = next_state.run_openroad(output_dir, openroad_path)
            global_step += 1
            print("delay = {}, area = {}".format(delay, area))
            # print("self.delay = {}, self.area = {}".format(self.delay, self.area))
            next_state.delay = delay
            next_state.area = area
            next_state.power = power
            next_state.update_fanout_map()
            fanout = next_state.fanout_map.max()
            print("try_step = {}".format(try_step))
            try_step += 1
            global_vars.flog.write("{}\t{:.2f}\t{:.2f}\t{}\t{}\t{}\t{}\t{}\t{}\t{:d}\t{:.2f}\n".format(
                        next_state.verilog_file_name.split(".")[0], 
                        next_state.delay, next_state.area, next_state.power, 
                        int(next_state.level), int(next_state.size), fanout,
                        global_step, cache_hit,
                        0, time.time() - global_vars.start_time))
            record_num += 1
            global_vars.flog.flush()
            print("record_num : {}/{}".format(record_num, step_count))
            if record_num >= step_count:
                sys.exit()
            if global_vars.initial_adder_type == 0: 
                if next_state.area < min_metric:
                    best_next_state = copy.deepcopy(next_state)
                    min_metric = next_state.area
            else:
                if next_state.area + next_state.delay <= min_metric:
                    best_next_state = copy.deepcopy(next_state)
                    min_metric = next_state.area + next_state.delay
            find = True
            if global_vars.initial_adder_type == 0:
                if next_state.area <= self.area:
                    pass
                else:
                    find = False
            if global_vars.initial_adder_type == 1 or global_vars.initial_adder_type == 2:
                if next_state.area + next_state.delay <= self.area + self.delay:
                    pass
                else:
                    find = False
            if find is False:
                self.available_choice_list.remove(random_choice)
                self.available_choice -=1
                assert self.available_choice == len(self.available_choice_list)
                continue
            self.cumulative_choices.append(action)
            return next_state
        
        return best_next_state

    def __repr__(self):
        return "State: {}, level: {}, choices: {}".format(
            hash(self), self.level, 
            self.cumulative_choices)
