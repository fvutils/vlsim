/****************************************************************************
 * vlsim_main.cpp
 ****************************************************************************/
#include <stdio.h>
#include "V${TOP}.h"

static V${TOP}		*prv_top;

typedef struct clockspec_s {
	unsigned char			*clk;
	unsigned char			clkval;
	unsigned int			offset;
	unsigned int			period;

	struct clockspec_s		*next;
} clockspec_t;

static unsigned long long		prv_simtime = 0;

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
			it->next = t->next;
			t->next = it;
		}
	}
}

int main(int argc, char **argv) {
	clockspec_t			*clockqueue = 0;
	unsigned int		num_clocks;
	unsigned long long	limit_simtime = (1 * 1000 * 1000);

	prv_top = new V${TOP}();

	clockspec_t			clockspec[] = {
		{
				&prv_top->clk,
				0,		// clkval
				0,		// offset
				10000, 	// period: 10ns
				0		// next
		},
		{
				&prv_top->int_clk,
				0,		// clkval
				0,		// offset
				20000, 	// period: 10ns
				0		// next
		}
	};

	// Populate clockqueue
	for (int i=0; i<sizeof(clockspec)/sizeof(clockspec_t); i++) {
		insert(&clockqueue, &clockspec[i]);
	}
		fprintf(stdout, "--> dump\n");
		{
			clockspec_t *t = clockqueue;
			while (t) {
				fprintf(stdout, "  %d: clk=%p next=%p\n", t->offset, t->clk, t->next);
				t = t->next;
			}
		}
		fprintf(stdout, "<-- dump\n");

	// Run clock loop
	fprintf(stdout, "prv_simtime=%lld limit_simtime=%lld\n", prv_simtime, limit_simtime);
	while (prv_simtime < limit_simtime && clockqueue) {
		fprintf(stdout, "--> dump (1)\n");
		{
			clockspec_t *t = clockqueue;
			while (t) {
				fprintf(stdout, "  %d: clk=%p\n", t->offset, t->clk);
				t = t->next;
			}
		}
		fprintf(stdout, "<-- dump (1)\n");
		clockspec_t *nc = clockqueue;
		if ((sizeof(clockspec)/sizeof(clockspec_t)) > 1) {
			clockqueue = clockqueue->next;
		}

		*nc->clk = nc->clkval;
		nc->clkval = (nc->clkval)?0:1;

		prv_top->eval();

		prv_simtime += nc->offset;
		nc->offset = nc->period;
		if ((sizeof(clockspec)/sizeof(clockspec_t)) > 1) {
			insert(&clockqueue, nc);
		}
		fprintf(stdout, "--> dump (2)\n");
		{
			clockspec_t *t = clockqueue;
			while (t) {
				fprintf(stdout, "  %d: clk=%p\n", t->offset, t->clk);
				t = t->next;
			}
		}
		fprintf(stdout, "<-- dump (2)\n");
	}

}
