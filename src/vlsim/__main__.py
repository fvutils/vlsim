'''
Created on Oct 1, 2019

@author: ballance
'''

import argparse
import subprocess
import shutil
import os
from string import Template

pkg_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(pkg_dir, "templates")

vl_args = ['/bin/sh', 'verilator', '--cc', '--exe']
#vl_args = ['verilator', '--cc', '--exe']
parser = argparse.ArgumentParser()
parser.add_argument("-f", action="append")
parser.add_argument("-F", action="append")
parser.add_argument("-j")
parser.add_argument("source_files", nargs="*")


args = parser.parse_args()

print("f_files=" + str(args.f))
print("F_files=" + str(args.F))

obj_dir='obj_dir'

j=1
if args.j is not None:
    j = args.j
    
    if j == "-1":
        # TODO: auto-probe
        j = 32
        
# Remove any existing object dir
shutil.rmtree(obj_dir)

# TODO: create testbench stub
os.mkdir(obj_dir)

vlsim_main_h = open(os.path.join(templates_dir, "vlsim_main.cpp"), "r")
vlsim_main = Template(vlsim_main_h.read())
vlsim_main_h.close()


if args.f is not None:
    for f in args.f:
        vl_args.append('-f')
        vl_args.append(f)
   
if args.F is not None: 
    for f in args.F:
        vl_args.append('-F')
        vl_args.append(f)

if args.source_files is not None:    
    for src in args.source_files:
        vl_args.append(src)
       
# Add in the main function
vl_args.append(os.path.join(obj_dir, "vlsim_main.cpp"))

print("args: " + str(vl_args))
ret = subprocess.call(vl_args)
#ret = subprocess.call(vl_args, shell=True)

if ret != 0:
    print("Error: verilator compilation failed")
    exit(1)

# Determine what the top module is
top=None
for f in os.listdir(obj_dir):
    if f.endswith(".mk") and f.find('_') == -1:
        top = f[1:-len(".mk")]
        
print("top=" + top)

# Now, create the real vlsim_main since we know the top-level
vars = {
    "TOP" : top}

vlsim_main_h = open(os.path.join(obj_dir, "vlsim_main.cpp"), "w")
vlsim_main_h.write(vlsim_main.safe_substitute(vars))
vlsim_main_h.close()


mk_args = ['make', '-j', str(j), '-C', obj_dir, 
           "-f", "V" + top + ".mk" ]
mk_log = open(os.path.join(obj_dir, "mk.log"), "w")
ret = subprocess.call(mk_args, stdout=mk_log, stderr=mk_log)
mk_log.close()

if ret != 0:
    print("Error: simulation image compilation failed.")
    mk_log = open(os.path.join(obj_dir, "mk.log"), "r")
    print(mk_log.read())
    mk_log.close()
    exit(1)

print("ret=" + str(ret))
