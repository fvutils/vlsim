/****************************************************************************
 * vlsim_main.cpp
 ****************************************************************************/
#include <stdio.h>
#include <verilated.h>
#include <dlfcn.h>
#if ${TRACE} == 1
#if ${TRACER_TYPE_FST} == 1
#include <verilated_fst_c.h>
#else
#include <verilated_vcd_c.h>
#endif
#endif
#if ${VPI} == 1
#include <verilated_vpi.h>
#endif
#if VM_COVERAGE == 1
#include <verilated_cov.h>
#endif
#include "V${TOP}.h"

static V${TOP}		*prv_top;

extern "C" {
	void vlog_startup_routines_bootstrap(void) __attribute__((weak));

	void vlog_startup_routines_bootstrap() {
    	// Do Nothing
    }
}

typedef struct clockspec_s {
	const char				*name;
	unsigned char			*clk;
	unsigned int			period;
	unsigned char			clkval;
	unsigned int			offset;
	unsigned int			p1, p2;

	struct clockspec_s		*next;
} clockspec_t;

static vluint64_t			prv_simtime = 0;

double sc_time_stamp() {
	return prv_simtime;
}

static void insert(clockspec_t **cq, clockspec_t *it) {
	if (!*cq) {
		*cq = it;
		it->next = 0;
	} else {
		if (it->offset <= (*cq)->offset) {
			(*cq)->offset -= it->offset;
			it->next = *cq;
			*cq = it;
		} else {
			clockspec_t *t = *cq;
			while (t->next && it->offset > t->offset) {
				it->offset -= t->offset;
				t = t->next;
			}
			it->offset -= t->offset;
			it->next = t->next;
			t->next = it;
		}
	}
}

static void printhelp(char **argv) {
	fprintf(stdout, "%s [arguments]\n");
	fprintf(stdout, "Verilated simulation image for module \"${TOP}\"\n");
	fprintf(stdout, "Runtime options:\n");
#if ${TRACE} == 1
	fprintf(stdout, "     +vlsim.trace                  		    Enable tracing\n");
#if ${TRACER_TYPE_FST} == 1
	fprintf(stdout, "     +vlsim.tracefile=<file>                   Specify tracefile name (default: simx.fst)\n");
#else
	fprintf(stdout, "     +vlsim.tracefile=<file>                   Specify tracefile name (default: simx.vcd)\n");
#endif
#endif
	fprintf(stdout, "     +verilator+debug                  		Enable debugging\n");
	fprintf(stdout, "     +verilator+debugi+<value>         		Enable debugging at a level\n");
	fprintf(stdout, "     +verilator+help                   		Display help\n");
	fprintf(stdout, "     +verilator+prof+threads+file+I<filename>  Set profile filename\n");
	fprintf(stdout, "     +verilator+prof+threads+start+I<value>    Set profile starting point\n");
	fprintf(stdout, "     +verilator+prof+threads+window+I<value>   Set profile duration\n");
	fprintf(stdout, "     +verilator+rand+reset+<value>             Set random reset technique\n");
	fprintf(stdout, "     +verilator+V                              Verbose version and config\n");
	fprintf(stdout, "     +verilator+version                        Show version and exit\n");
}

int main(int argc, char **argv) {
	clockspec_t			*clockqueue = 0;
	unsigned int		num_clocks;
//	unsigned long long	limit_simtime = (100 * 1000 * 1000 * 1000);
	unsigned long long	limit_simtime = (1000 * 1000 * 1000);
	bool				trace_en = false;
	const char			*trace_file = 0;
//	limit_simtime *= 100;
	limit_simtime *= 1;
#if ${TRACER_TYPE_FST} == 1
	VerilatedFstC		*tfp = 0;
#else
	VerilatedVcdC		*tfp = 0;
#endif

	Verilated::commandArgs(argc, argv);

	prv_top = new V${TOP}();
#if ${VPI} == 1
	// Turn off fatal VPI errors
	Verilated::fatalOnVpiError(false);
#endif

	for (int i=1; i<argc; i++) {
		if (!strcmp(argv[i], "+vlsim.trace")) {
			trace_en = true;
		} else if (!strncmp(argv[i], "+vlsim.tracefile=", strlen("+vlsim.tracefile="))) {
			trace_file = &argv[i][strlen("+vlsim.tracefile=")];
		} else if (!strncmp(argv[i], "+vlsim.timeout=", strlen("+vlsim.timeout="))) {
			char *eptr;
			unsigned long long mfactor;
			limit_simtime = strtoul(&argv[i][strlen("+vlsim.timeout=")], &eptr, 10);

			if (!strcasecmp(eptr, "ps")) {
				mfactor = 1;
			} else if (!strcasecmp(eptr, "ns")) {
				mfactor = 1000;
			} else if (!strcasecmp(eptr, "us")) {
				mfactor = 1000000;
			} else if (!strcasecmp(eptr, "ms")) {
				mfactor = 1000000000;
			} else if (!strcasecmp(eptr, "s")) {
				mfactor = 1000000000000;
			} else {
				fprintf(stdout, "Error: unknown timeout units \"%s\"\n", eptr);
				exit(1);
			}
			limit_simtime *= mfactor;
		}
	}

#if ${VPI} == 1
	// Load any PLI modules
	for (int i=1; i<argc; i++) {
		if (!strncmp(argv[i], "+vpi=", 5)) {
			const char *vpi_lib = &argv[i][5];
			fprintf(stdout, "Note: Loading VPI library \"%s\"\n", vpi_lib);
			void *lib = dlopen(vpi_lib, RTLD_LAZY);
			if (!lib) {
				fprintf(stdout, "Error: failed to load VPI library - \"%s\"\n", dlerror());
				exit(1);
			}
			void *startup_s = dlsym(lib, "vlog_startup_routines");
			if (!startup_s) {
				fprintf(stdout, "Error: failed to find symbol \"vlog_startup_routines\"\n");
				exit(1);
			}
			typedef void (*init_f)();
			init_f *startup_f = (init_f *)startup_s;
			for (int i=0; startup_f[i]; i++) {
				startup_f[i]();
			}
		}
	}
#endif

#if ${TRACE} == 1
	if (trace_en) {
		fprintf(stdout, "Note: enabling tracing\n");
		Verilated::traceEverOn(true);
#if ${TRACER_TYPE_FST} == 1
		tfp = new VerilatedFstC();
#else
		tfp = new VerilatedVcdC();
#endif
		tfp->set_time_unit("ps");
		tfp->set_time_resolution("ps");
		prv_top->trace(tfp, 99);
		if (!trace_file) {
#if ${TRACER_TYPE_FST} == 1
			trace_file = "simx.fst";
#else
			trace_file = "simx.vcd";
#endif
		}
		tfp->open(trace_file);
	} else {
	}
#endif

	clockspec_t			clockspec[] = {
${CLOCKSPEC}
	};

	// Populate clockqueue
	for (int i=0; i<sizeof(clockspec)/sizeof(clockspec_t); i++) {
		clockspec[i].clkval = 1;
		clockspec[i].offset = 0;
		clockspec[i].p1 = clockspec[i].period/2;
		clockspec[i].p2 = clockspec[i].period-(clockspec[i].period/2);
		insert(&clockqueue, &clockspec[i]);
	}
//		fprintf(stdout, "--> dump\n");
//		{
//			clockspec_t *t = clockqueue;
//			while (t) {
//				fprintf(stdout, "  %d: clk=%p next=%p\n", t->offset, t->clk, t->next);
//				t = t->next;
//			}
//		}
//		fprintf(stdout, "<-- dump\n");

#if ${VPI} == 1
	vlog_startup_routines_bootstrap();
	// Notify VPI applications that simulation is about to start
	VerilatedVpi::callCbs(cbStartOfSimulation);
#endif

	// Run clock loop
	while (prv_simtime < limit_simtime && clockqueue && !Verilated::gotFinish()) {
		clockspec_t *nc = clockqueue;
		if ((sizeof(clockspec)/sizeof(clockspec_t)) > 1) {
			clockqueue = clockqueue->next;
		}

		prv_simtime += nc->offset;
		*nc->clk = nc->clkval;
		nc->clkval = (nc->clkval)?0:1;

#if ${VPI} == 1
		// With VPI, we evaluate the design until
		// no more scheduled WriteSynch callbacks are called
		bool again = false;
		do {
#endif
			prv_top->eval();

#if ${VPI} == 1
            VerilatedVpi::callValueCbs();

            // Call registered Read-Write callbacks
            again = VerilatedVpi::callCbs(cbReadWriteSynch);

            // Call Value Change callbacks as cbReadWriteSynch
            // can modify signals values
            VerilatedVpi::callValueCbs();
		} while (again);
#endif

#if ${VPI} == 1
		// Call read-only and timed callbacks
        VerilatedVpi::callCbs(cbReadOnlySynch);
        VerilatedVpi::callTimedCbs();
#endif

#if ${TRACE} == 1
		if (tfp) {
			tfp->dump(prv_simtime);
		}
#endif

#if ${VPI} == 1
        // Call registered NextSimTime
        // It should be called in new slot before everything else
        VerilatedVpi::callCbs(cbNextSimTime);
#endif

		nc->offset = (nc->clkval)?nc->p1:nc->p2;
		if ((sizeof(clockspec)/sizeof(clockspec_t)) > 1) {
			insert(&clockqueue, nc);
		}
	}

#if ${VPI} == 1
    VerilatedVpi::callCbs(cbEndOfSimulation);
#endif

#if ${TRACE} == 1
	if (tfp) {
		tfp->close();
	}
#endif

#if VM_COVERAGE == 1
	VerilatedCov::write();
#endif
}
