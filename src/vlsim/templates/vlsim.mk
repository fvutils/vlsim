#****************************************************************************
#* vlsim.mk
#*
#* This Makefile builds the simulator image, and primarily exists to ensure
#* that we can customize the compilation command
#****************************************************************************

VLSIM_OUTFILE?=vlsim

include V${TOP}.mk

all : $(VK_USER_OBJS) $(VK_GLOBAL_OBJS) $(VM_PREFIX)__ALL.a $(VM_HIER_LIBS)
	$(LINK) $(LDFLAGS) $(VK_USER_OBJS) $(VK_GLOBAL_OBJS) \
		-Wl,--whole-archive $(VM_PREFIX)__ALL.a -Wl,--no-whole-archive \
		$(LOADLIBES) $(LDLIBS) $(LIBS) $(SC_LIBS) -o $(VLSIM_OUTFILE)


