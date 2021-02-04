#****************************************************************************
#* vlsim::__main__.py
#*
#*
#****************************************************************************

import argparse
import os
import shutil
from string import Template
import subprocess
import sys

from vlsim import vl_options
from _ast import arg

def main():
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(pkg_dir, "templates")

    # Determine VERILATOR_ROOT either directly or from path
    if 'VERILATOR_ROOT' not in os.environ:
        for p in os.environ["PATH"].split(':'):
            if os.path.exists(os.path.join(p, "verilator")) or os.path.exists(os.path.join(p, "verilator.exe")):
                verilator_root = os.path.join(
                    os.path.dirname(p), "share", "verilator")
                break
               
    else:
        verilator_root = os.environ['VERILATOR_ROOT']
        
    verilator=os.path.join(
        os.path.dirname(os.path.dirname(verilator_root)), "bin", "verilator")
    verilator_bin=os.path.join(
        os.path.dirname(os.path.dirname(verilator_root)), "bin", "verilator_bin")
        
    vl_args = [verilator_bin, "--cc", "--exe"]
    parser = argparse.ArgumentParser(description="Verilator front-end")
    parser.add_argument("-clkspec", action="append",
            help="Specifies a clock. <path>=<period>[:<offset>]")
#    parser.add_argument("-j")
    parser.add_argument("-sv", action="append_const", dest="args", const="-sv")
    parser.add_argument("-Wno-fatal", action="append_const", dest="args", const="-Wno-fatal")
    parser.add_argument('-o', default='simv')
    
    vl_options.configure_vl_options(parser, verilator)
    parser.add_argument("source_files", nargs="*")
    
    argv = []
    argc = len(sys.argv)
    i=1
    while i < argc:
        arg=sys.argv[i]
        if arg.startswith("+"):
            vl_args.append(arg)
        elif arg.startswith("-D") or arg.startswith("-I") or arg.startswith("-G"):
            vl_args.append(arg)
        elif arg == "-f" or arg == "-F":
            vl_args.append(arg)
            i += 1
            vl_args.append(sys.argv[i])
        elif arg == "-LDFLAGS" or arg == "-CFLAGS":
            vl_args.append(arg)
            i += 1
            vl_args.append(sys.argv[i])
        elif arg.startswith("-Wno-"):
            vl_args.append(arg)
        else:
            argv.append(arg)
        i += 1
    
    args = parser.parse_args(argv)
    
    timescale_m = {
        "s" :  1000000000000,
        "ms" : 1000000000,
        "us" : 1000000,
        "ns" : 1000,
        "ps" : 1};
    
    clkspec=""
    if args.clkspec is not None:
        for i in range(len(args.clkspec)):
            cs=args.clkspec[i]
            if cs.find("=") == -1:
                print("Error: clkspec \"" + cs + "\" is missing an '='")
                exit(1)
            eq_idx = cs.find("=")
                
            offset="0ns"
            name=cs[:cs.find("=")]
            offset_c=cs.find(":", eq_idx)
            if offset_c != -1:
                offset=cs[offset_c+1:]
                period=cs[cs.find("=")+1:offset_c]
            else:
                period=cs[cs.find("=")+1:]

            print("offset=\"" + offset + "\" period=\"" + period + "\"")
            
            if len(period) < 2:
                print("Error: malformed clock period \"" + period + "\"")
                exit(1)
                
            period_u = period[-2:]
            period_n = float(period[:-2])
            if not period_u in timescale_m.keys():
                print("Error: unknown clockspec units \"" + period_u + "\"")
                exit(1)
                
            period_n *= timescale_m[period_u]

            offset_u = offset[-2:]
            offset_n = float(offset[:-2])
            if not offset_u in timescale_m.keys():
                print("Error: unknown clockspec units \"" + offset_u + "\"")
                exit(1)
                
            offset_n *= timescale_m[offset_u]
                
            spec = "\t\t{.name=\"" + name + "\", .clk=&prv_top->" + name + ", .period=" + str(int(period_n)) + ", .offset=" + str(int(offset_n)) + "}"
            if i+1 < len(args.clkspec):
                spec += ",\n"
            else:
                spec += "\n"
            clkspec += spec
    else:
        print("Error: no clocks specified")
        exit(1)
    
    vl_args.append('-o')
    vl_args.append('../' + args.o)

    vl_args.append('-LDFLAGS')
    vl_args.append('-ldl')
    vl_args.append('-LDFLAGS')
    vl_args.append('-rdynamic')
    
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
    
    if args.args is not None:
        if isinstance(args.args, str):
            vl_args.append(args.args)
        else:
            for arg in args.args:
                vl_args.append(arg)
    
    if args.source_files is not None:    
        for src in args.source_files:
            vl_args.append(src)
           
    # Add in the main function
    vl_args.append(os.path.join(obj_dir, "vlsim_main.cpp"))

    ret = subprocess.call(vl_args)
    
    if ret != 0:
        print("Error: verilator compilation failed")
        exit(1)
    
    # Determine what the top module is
    top=None
    for f in os.listdir(obj_dir):
        if f.endswith(".mk") and not f.endswith('_classes.mk'):
            top = f[1:-len(".mk")]
            break
            
    if top is None:
        print("Error: failed to discover name of root module")
        exit(1)
            
    # Now, create the real vlsim_main since we know the top-level
    if '--trace' in vl_args or "--trace-fst" in vl_args:
        trace="1"
    else:
        trace="0"
        
    if "--trace-fst" in vl_args:
        tracer_type_fst = "1"
    else:
        tracer_type_fst = "0"

    if "--vpi" in vl_args:
        vpi = "1"
    else:
        vpi = "0"
        
    if "--coverage" in vl_args:
        coverage = "1"
    else:
        coverage = "0"
        
    template_vars = {
        "TOP" : top,
        "CLOCKSPEC" : clkspec,
        "TRACE" : trace,
        "TRACER_TYPE_FST" : tracer_type_fst,
        "VPI" : vpi,
        "COVERAGE" : coverage
    }
    
    vlsim_main_h = open(os.path.join(obj_dir, "vlsim_main.cpp"), "w")
    vlsim_main_h.write(vlsim_main.safe_substitute(template_vars))
    vlsim_main_h.close()
   
    vlsim_mk_f = open(os.path.join(templates_dir, "vlsim.mk"), "r")
    vlsim_mk_t = Template(vlsim_mk_f.read())
    vlsim_mk_f.close()
    
    vlsim_mk = open(os.path.join(obj_dir, "vlsim.mk"), "w")
    vlsim_mk.write(vlsim_mk_t.safe_substitute(template_vars))
    vlsim_mk.close()
    
    mk_args = ['make', '-j', str(j), '-C', obj_dir, 
               "-f", "vlsim.mk", "all" ]
    mk_log = open(os.path.join(obj_dir, "mk.log"), "w")
    os.environ['VLSIM_OUTFILE'] = os.path.abspath(args.o)
    ret = subprocess.call(mk_args, stdout=mk_log, stderr=mk_log)
    mk_log.close()
    
    if ret != 0:
        print("Error: simulation image compilation failed.")
        mk_log = open(os.path.join(obj_dir, "mk.log"), "r")
        print(mk_log.read())
        mk_log.close()
        exit(1)
    
    exit(0)

if __name__ == "__main__":
    main()

