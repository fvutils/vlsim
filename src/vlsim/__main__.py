#****************************************************************************
#* vlsim::__main__.py
#*
#*
#****************************************************************************

import argparse
import subprocess
import shutil
import os
from string import Template

pkg_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(pkg_dir, "templates")

#vl_args = ['/bin/sh', 'verilator', '--cc', '--exe']
#vl_args = ['verilator_bin', '--cc', '--exe']

# Determine VERILATOR_ROOT either directly or from path
if 'VERILATOR_ROOT' not in os.environ:
    for p in os.environ["PATH"].split(':'):
        if os.path.exists(os.path.join(p, "verilator")) or os.path.exists(os.path.join(p, "verilator.exe")):
            verilator_root = os.path.join(
                os.path.dirname(p), "share", "verilator")
            break
           
else:
    verilator_root = os.environ['VERILATOR_ROOT']
    
outname='simv'
    
vl_args = [os.path.join(
    os.path.dirname(os.path.dirname(verilator_root)), 
    "bin", "verilator_bin"), '--cc', '--exe', '-o', '../' + outname]
parser = argparse.ArgumentParser()
parser.add_argument("-f", action="append")
parser.add_argument("-F", action="append")
parser.add_argument("-clock", action="append")
parser.add_argument("-j")
parser.add_argument('-o', default='simv')
parser.add_argument("source_files", nargs="*")


args = parser.parse_args()

if args.clock is None:
    print("Error: no clocks specified")
    exit(1)

vl_args.append('-o')
vl_args.append('../' + args.o)

obj_dir='obj_dir'

j=1
if args.j is not None:
    j = args.j
    
    if j == "-1" or j == "auto":
        # TODO: auto-probe
        j = 32
        
# Remove any existing object dir
if os.path.isdir(obj_dir):
    shutil.rmtree(obj_dir)

os.makedirs(obj_dir)

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


#environ = os.environ
#environ['VERILATOR_ROOT'] = verilator_root    
print("args: " + str(vl_args))
ret = subprocess.call(vl_args)
print("ret=" + str(ret))
#ret = subprocess.call(vl_args, shell=True)

if ret != 0:
    print("Error: verilator compilation failed")
    exit(1)

# Determine what the top module is
top=None
for f in os.listdir(obj_dir):
    if f.endswith(".mk") and f.find('_') == -1:
        top = f[1:-len(".mk")]
        
if top is None:
    print("Error: failed to discover name of root module")
    exit(1)
        
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
