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

class Node(object):

    def __init__(self):
        self.parent = None
        self.children = []

        self.visit_times = 0
        self.quality_value = 0.0
        self.best_reward = -sys.maxsize

        self.state = None

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def get_parent(self):
        return self.parent

    def set_parent(self, parent):
        self.parent = parent

    def get_children(self):
        return self.children

    def get_visit_times(self):
        return self.visit_times

    def set_visit_times(self, times):
        self.visit_times = times

    def visit_times_add_one(self):
        self.visit_times += 1

    def get_quality_value(self):
        return self.quality_value

    def set_quality_value(self, value):
        self.quality_value = value

    def quality_value_add_n(self, n):
        self.quality_value += n
    
    def update_best_reward(self, n):
        self.best_reward = max(self.best_reward, n)
    
    def get_best_reward(self):
        return self.best_reward

    def is_all_expand(self):
        return len(self.children) == self.state.available_choice

    def add_child(self, sub_node):
        sub_node.set_parent(self)
        self.children.append(sub_node)

    def __repr__(self):
        return "Node: {}, Q/N: {}/{}, best: {}, state: {}".format(
            hash(self), self.quality_value, self.visit_times, self.best_reward, self.state)