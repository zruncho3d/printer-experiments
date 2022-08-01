#!/usr/bin/env python3
# Script to drive a complete accelerometer-based resonance test on a printer
# with the Moonraker API to Klipper, from a nearby computer.
#
# For a quick way to see the options, invoke this program with the help option:
#   ./run_accelerometer_test.py
#
# Typical usage looks something like this:
#   ./run_resonance_test.py myprinter.local mytestname --klipper-path ~/klipper
#   open mytestname/*.png
#
# The raw data and analysis pictures will be placed into a created directory
# matching the test name.
#
# Does the following:
# - home a printer
# - trigger resonance-testing measurements
# - copy the results from a remote system to a local folder
# - graph and locally store those results
#
# After completion, run open <testname>/*.png on Mac to view all files.
# Must be on a post-2020 version of Klipper or other one with resonance
# testing code integrated, plus have a connected and configured
# accelerometer.
# See https://www.klipper3d.org/Measuring_Resonances.html for more about this.

import argparse
import os
import requests
import subprocess
import time

# See https://github.com/Arksine/moonraker/blob/master/docs/web_api.md

DEFAULT_AXES = ["x", "y"]

# Set this high enough to handle any command you'd run.
# Note, however, that Moonraker by default throws a 200 after exactly
# one minute, even with this value set to exceed one minute.
READ_TIMEOUT=180

# Determined empirically by watching /tmp/moonraker.conf, then adding a few
# seconds.  If insufficient, you'll just get a hang.
AFTER_TIMEOUT_WAIT_FOR_RESONANCE_TEST_S = 91.0


def run_gcode(printer, gcode):
    """Run a gcode command to completion and return the result.
    https://github.com/Arksine/moonraker/blob/master/docs/web_api.md#run-a-gcode
    """
    r = requests.post("http://" + args.printer + "/printer/gcode/script?script=" + gcode, timeout=(1, READ_TIMEOUT))
    #print(r.status_code)
    # Disabled for now to workaround 60-second presumably-Moonraker timeout
    #assert(r.status_code == 200)
    return r


parser = argparse.ArgumentParser(description="Automate a resonance test using Klipper and an ADXL.")
parser.add_argument('printer', help="Printer address, whether IP or zeroconf - something like mainsailos.local")
parser.add_argument('testname', help="Name of test - something like changed_mounting_location")
parser.add_argument('--klipper-path', default="~/Projects/src/klipper")
parser.add_argument('--username', default="pi", help="Username corresponding to printer connection")
parser.add_argument('--axes', metavar='N', type=str, nargs='+', default=DEFAULT_AXES, help="Axes")
parser.add_argument("--no-testing", help="Skip remote resonance-testing steps", action="store_true")
parser.add_argument("--no-processing", help="Skip local processing steps", action="store_true")
parser.add_argument("--no-clear", help="Skip remote file-clear step", action="store_true")
args = parser.parse_args()

start_time = time.time()

klipper_scripts_path=os.path.join(os.path.expanduser(args.klipper_path), 'scripts')

assert os.path.exists(klipper_scripts_path)

if not args.no_clear:
    print("Clearing remote .csv files.")
    # https://www.tutorialspoint.com/How-to-copy-a-file-to-a-remote-server-in-Python-using-SCP-or-SSH
    p = subprocess.Popen(["ssh", args.username + "@" + args.printer, "rm", "/tmp/*.csv"])
    sts = os.waitpid(p.pid, 0)

if not args.no_testing:
    print("Homing printer.")
    run_gcode(args.printer, "G28")

    for axis in args.axes:
        print("Testing resonances in " + axis + " axis.")
        gcode_start_time = time.time()
        result = run_gcode(args.printer, "TEST_RESONANCES AXIS={value} OUTPUT=raw_data".format(value = axis))
        gcode_elapsed = time.time() - gcode_start_time
        if (result.status_code == 504 and gcode_elapsed >= 59.0 and gcode_elapsed <= 65.0):
            print("Delaying a bit, since the g-code command timed out.")
            time.sleep(AFTER_TIMEOUT_WAIT_FOR_RESONANCE_TEST_S)

if not args.no_processing:
    if not os.path.exists(args.testname):
        print("Creating directory")
        os.mkdir(args.testname)

    print("Copying files")
    # https://www.tutorialspoint.com/How-to-copy-a-file-to-a-remote-server-in-Python-using-SCP-or-SSH
    p = subprocess.Popen(["scp", args.username + "@" + args.printer + ":/tmp/*.csv", args.testname])
    sts = os.waitpid(p.pid, 0)

    print("Running processing scripts")
    for axis in args.axes:
        subprocess.check_output("python3 {klipper_scripts_path}/graph_accelerometer.py" \
            " {testname}/raw_data_{axis}_*.csv -a {axis} -o {testname}/{axis}_raw_{testname}.png" \
            .format(klipper_scripts_path = klipper_scripts_path, testname = args.testname, axis = axis), stderr=subprocess.STDOUT, shell=True)

        subprocess.check_output("python3 {klipper_scripts_path}/calibrate_shaper.py" \
            " {testname}/raw_data_{axis}*.csv -o {testname}/calibrate_{axis}_{testname}.png" \
            .format(klipper_scripts_path = klipper_scripts_path, testname = args.testname, axis = axis), stderr=subprocess.STDOUT, shell=True)

print("Test completed.")
print("To view files, run:\n\topen " + args.testname + "/*.png")
print("--- %s seconds ---" % round(time.time() - start_time, 2))
