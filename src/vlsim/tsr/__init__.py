from tsr.plusarg_info import PlusargInfo, PlusargType

print("Note: loaded vlsim tsr plugin")

import tsr
import os

vlsim_tsr_dir = os.path.dirname(os.path.abspath(__file__))

vlsim = tsr.EngineInfo(
    "vlsim",
    os.path.join(vlsim_tsr_dir, "mkfiles", "engine_vlsim.mk"), [
        PlusargInfo("vlsim.clkspec", 
                    "Specifies a clock for vlsim to generate", 
                    PlusargType.Str)
    ])
    

tsr.Registry.inst().register_engine(vlsim)
