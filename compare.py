#!/usr/bin/env python3
# Use a Mann-Whitney test to compare data from two unknown distributions.
# For example: compare numbers of iterations to achive bed probing within a tolerance.

import argparse
import json
import time

from termcolor import colored, cprint
from scipy.stats import mannwhitneyu


DEFAULT_P_TARGET = 0.01


def run_compare(args):
    start_time = time.time()

    with(open(args.one, 'r') as f1):
        d1 = json.load(f1)
    with(open(args.two, 'r') as f2):
        d2 = json.load(f2)
    assert(len(d1) == len(d2))

    if args.show_data:
        print("%s:\n %s" % (args.one, d1))
        print("%s:\n %s" % (args.two, d2))

    results = mannwhitneyu(d1, d2)
    pvalue = results.pvalue
    if pvalue < args.p_target:
        # If pvalue is lower, we have more confidence than necessary.
        print(colored('Null hypothesis is rejected; data is sufficiently different, with p-value %0.6f' % pvalue, 'green'))
    else:
        print(colored('Data is insufficient to reject the null hypothesis, with p-value %0.4f' % pvalue, 'red'))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a statistical comparison between two Klipper-experiment data sets.")
    parser.add_argument('one', help="Input file one; must be JSON list data")
    parser.add_argument('two', help="Input file two; must be JSON list data")
    parser.add_argument('--show_data', help="Print out data", action='store_true')
    parser.add_argument('--verbose', help="Use more-verbose debug output", action='store_true')
    parser.add_argument('--p_target', help="Target p-value at which to declare victory", default=DEFAULT_P_TARGET)
    args = parser.parse_args()

    run_compare(args)