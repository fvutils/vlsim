#****************************************************************************
#* engine_vlsim.mk
#*
#* TSR build and run definitions and rules for TSR
#*
#****************************************************************************

#********************************************************************
#* Compile rules
#********************************************************************

ifneq (1,$(RULES))

include $(TSR_MKFILES_DIR)/hdlsim_common.mk
include $(TSR_MKFILES_DIR)/plusargs.mk


ifeq (ms,$(findstring ms,$(TIMEOUT)))
  timeout=$(shell expr $(subst ms,,$(TIMEOUT)) '*' 1000000)
else
  ifeq (us,$(findstring us,$(TIMEOUT)))
    timeout=$(shell expr $(subst us,,$(TIMEOUT)) '*' 1000)
  else
    ifeq (ns,$(findstring ns,$(TIMEOUT)))
      timeout=$(shell expr $(subst ns,,$(TIMEOUT)) '*' 1)
    else
      ifeq (s,$(findstring s,$(TIMEOUT)))
        timeout=$(shell expr $(subst s,,$(TIMEOUT)) '*' 1000000000)
      else
        timeout=error: unknown $(TIMEOUT)
      endif
    endif
  endif
endif

#********************************************************************
#* Capabilities configuration
#********************************************************************
TSR_VLOG_DEFINES += HAVE_HDL_DUMP HAVE_HDL_CLKGEN IVERILOG

SIM_LANGUAGE=verilog

BUILD_COMPILE_TARGETS += vlsim_compile

ifeq (,$(TB_MODULES))
ifneq (,$(TB_MODULES_HDL))
TB_MODULES = $(TB_MODULES_HDL) $(TB_MODULES_HVL)
else
TB_MODULES = $(TB)
endif
endif

TSR_RUN_TARGETS += vlsim_run
CLKSPECS=$(call get_plusarg,vlsim.clkspec,$(TSR_PLUSARGS))

ifeq (,$(CLKSPECS))
	$(error "No clocks specified with +vlsim.clkspec=<clock>:<period>
endif

TSR_VLOG_FLAGS += $(foreach s,$(CLKSPECS),-clkspec $(subst :,=,$(s)))

TSR_VLOG_FLAGS += $(foreach d,$(TSR_VLOG_DEFINES),+define+$(d))
TSR_VLOG_FLAGS += $(foreach i,$(TSR_VLOG_INCLUDES),+incdir+$(call native_path,$(i)))

else # Rules

#********************************************************************
#* Query interface to provide engine-specific details
#********************************************************************
ivl-help: ivl-info ivl-plusargs

ivl-info:
	@echo "Icarus Verilog"
	
ivl-plusargs: hdlsim-plusargs
	
#********************************************************************
#* Build/Run rules
#********************************************************************



vlsim_compile : 
	$(Q)echo "TSR_PLUSARGS: $(TSR_PLUSARGS)"
	$(Q)$(TSR_PYTHON) -m vlsim -sv --top-module $(TSR_TB_MODULES_HDL) -Wno-fatal \
		$(TSR_VLOG_FLAGS) $(TSR_VLOG_ARGS_HDL)

TSR_RUN_ARGS += +timeout=$(timeout)
	
ifeq (true,$(DEBUG))
TSR_RUN_ARGS += +dumpvars
endif

vlsim_run :
	$(Q)$(TSR_RUN_ENV_VARS_V)$(TSR_BUILD_DIR)/simv \
		$(foreach l,$(VPI_LIBRARIES),-m $(l)) \
		$(TSR_RUN_FLAGS) \
		$(TSR_BUILD_DIR)/simv.vvp \
		$(TSR_RUN_ARGS) $(REDIRECT)
		
include $(TSR_MKFILES_DIR)/hdlsim_common.mk
	
endif # Rules

