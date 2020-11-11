'''
Created on Oct 3, 2019

@author: ballance
'''
from argparse import Action

class append_arg(Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, nargs, **kwargs)
    def __call__(self, parser, namespace, values, option_string=None):
        if hasattr(namespace, "args"):
            if namespace.args is None:
                namespace.args = []
            namespace.args.append(option_string)
            namespace.args.append(values)
        else:
            setattr(namespace, "args", [option_string, values])

def configure_vl_options(parser, verilator):
    # Read verilator options
    fp = open(verilator, "r")
    
    # Options we don't want to make available
    filter_list = ["--cc", "-sc", "-o", "--exe", "--help", 
                   "--debugi", "--debugi-<srcfile>",
                   "--dump-treei", "--dump-treei-<srcfile>"]
    
    found_begin = False
    
    for line in fp.readlines():
        if found_begin:
            if line.find("head1 VERILATION ARGUMENTS") != -1:
                break

            line = line.strip()            
            if line.find("--") != -1:
                if line.find(" <") != -1:
                    option=line[:line.find(" <")]
                    arg=line[line.find(" <")+2:line.find(">")]
                    desc_text = line[line.find(">")+1:].strip()
#                    print("Option with regular argument: " + option + " ; " + arg + " ; " + desc_text)

                    if option not in filter_list:
                        parser.add_argument(option, 
                            action=append_arg, 
                            help=desc_text)
                elif line.find("<") != -1:
                    print("Option with funny argument: " + line)
                else:
                    option=line[:line.find(' ')].strip()
                    desc_text = line[line.find(' '):].strip()
                    if option not in filter_list:
                        parser.add_argument(option, 
                            action="append_const", 
                            dest="args",
                            const=option,
                            help=desc_text)
        elif line.find("ARGUMENT SUMMARY") != -1:
            found_begin = True
            
    fp.close()
    pass
