# Printer Experiments

## Make it better, with data.  And confidence.

![Front](Images/i_have_to.png)

**This repo is a collection of scripts and notes for running reproducible experiments with printers.**

You can run a single gcode action a whole bunch of times, conveniently, and record console outputs of interest from it.

You can run one of multiple pre-defined tests, or add your own in Python.  

You can compare the before-and-after results from a test, with statistical confidence, to see if what you did... did anything at all.

Conveniently, the code stays local to your laptop, since it uses REST API calls to Moonraker (the web API for Klipper).  There's no data to move after the test.  It's all right there.  And it's easier to edit this way.

**You can ask questions like:**
* Is my printer homing more effectively, after tightening a loose screw?
* Does better microstepping lead to better bed leveling?
* Should I pay more for spherical joints or use flexible printed ones?
* How does my printer compare to another, at least in bed-leveling speed?
* Is something off with my printer, compared to how it used to work?

With your own added tests, the Python codebase can help to enable even-more-interesting questions like:
* How fast can my printer reliably run?
* After 10K probing clicks, does my probe still work?
* How repeatable is sensorless homing?

**Let's make it concerete. Here's an example session.**

Say that you realized your bed and probe offsets were configured wrong, on a triple-bed-leveling printer, like a [Tri-Zero](https://github.com/zruncho3d/tri-zero) or [Trident](https://vorondesign.com/voron_trident), and you wanted to see if your changes made things better.

Install script dependencies locally, on a system with Python:
```bash
pip install requests termcolor scipy
```

You can now run the script.  To see what options it has, run with the `-h` parameter:

```bash
usage: run_test.py [-h] [--test_type {probe_accuracy,z_tilt_adjust_no_reset,z_tilt_adjust_moved,z_tilt_adjust_moved_randomized}] [--verbose]
                   [--iterations ITERATIONS] [--command COMMAND] [--stats] [--output] [--output_path OUTPUT_PATH]
                   [--z_tilt_random_move_min Z_TILT_RANDOM_MOVE_MIN] [--z_tilt_random_move_max Z_TILT_RANDOM_MOVE_MAX]
                   printer

Run an automated, multi-iteration Klipper test.

positional arguments:
  printer               Printer address, whether IP or zeroconf - something like mainsailos.local

optional arguments:
  -h, --help            show this help message and exit
  --test_type {probe_accuracy,z_tilt_adjust_no_reset,z_tilt_adjust_moved,z_tilt_adjust_moved_randomized}
                        Test type
  --verbose             Use more-verbose debug output
  --iterations ITERATIONS
                        Number of test iterations
  --command COMMAND     Command to execute
  --stats               Show stats
  --output              Write output data?
  --output_path OUTPUT_PATH
                        Directory at which to write output data
  --z_tilt_random_move_min Z_TILT_RANDOM_MOVE_MIN
                        When jittering Z_TILT test, minimum of range to move
  --z_tilt_random_move_max Z_TILT_RANDOM_MOVE_MAX
                        When jittering Z_TILT test, maximum of range to move

```

First, run a baseline test.  Invoking the `run_test.py` script looks like this:

```bash
./run_test.py double-dragon.local \
  --test_type z_tilt_adjust_moved_randomized \
  --iterations 10 \
  --output \
  --output_path x0/baseline.json
```

The `run_test.py` script can:
* connect to a printer running Moonraker+Klipper
* trigger multiple iterations of given test type
* extract the key value(s) from the console from each iteration
* automatically run start and stop gcodes
* prints stats at the end

This particular tests connects to a printer named `double-dragon.local`, runs a test that force-moves one axis a random amount, triggers a Z_TILT_ADJUST cycle to automatically level the bed, 10 times, then writes the list of output values to local file called `x0/baseline.json`.

The output will look something like this:

```bash
Starting test.
Using random distance: 5.707
> Result: 2
Using random distance: 4.440
> Result: 2

...

Test completed.
Ran 10 iterations.
Data: [3, 2, 3, 2, 3, 3, 2, 3, 3, 3]
--- 305.03 seconds total; 30.50 per iteration ---
```

Great! Then, you'd make the Klipper config changes and restart Klipper to apply them.

```bash
./run_test.py double-dragon.local \
  --test_type z_tilt_adjust_moved_randomized \
  --iterations 10 \
  --output \
  --output_path x0/modified.json
```

After it runs, you now have a second file in `x0/modified.json` and are ready to compare the two using the `compare.py` script:

```bash
./compare.py x0/baseline.json x0/modified.json --show_data
```

The output will say whether there was enough data to conclude that the two input data sets are drawn from a different distribution, with the given p-value.  p=0.05 is a good starting point, and anything less than this gives much greater confidence.  For the curious the statistical test in use is called the [Mann-Whitney U Test](https://en.wikipedia.org/wiki/Mann%E2%80%93Whitney_U_test), where we want to compare two data sets that are not necessarily from a normal distribution.

Here's an example output, with real data taken from [Double Dragon]() after Zruncho realized that the `probe` and `z_bed_tilt` sections in the Klipper config had wrong values, and changed them each by a few mm.  Clearly there was an improvement, but was it staistically sound?  In other words, should we trust it, or get more data?

```bash
x0/baseline.json:
 [3, 2, 3, 2, 3, 3, 2, 3, 3, 3]
x0/modified.json:
 [2, 2, 2, 2, 2, 2, 2, 2, 2, 2]

Null hypothesis is rejected.
Data is sufficiently different, with p-value 0.001617
```

Hot damn!  Even with only 10 tests, we have a strong confidence that there's a statistically meaningful difference.  With high certainty, the change worked.

This is a quick example of the kind of thing you can now test, with low pain, in only a few commands.

## Best Practices

Make sure to name every change with enough specificity to know what you did and why, and maybe even when.  For example, the run above was not called `modified.json`, it was
`2022-02-27-updated_z_positions_2_7_10iters.json` - to capture the relevant parameters.

And every time you run a test, make a bash script for it, and list the key parameters before vs after, so you can refer to the change later.

```bash
printer-experiments  (main) 15748 $ cat gen_64x_faster_probe.sh
#!/usr/bin/env bash
# Speed up the probing.
mkdir -p x0
./run_test.py double-dragon.local \
  --test_type z_tilt_adjust_moved_randomized \
  --iterations 50 \
  --output \
  --stats \
  --output_path x0/2022-02-27-even_faster_probing_0_1_50iters.json
```

## Install & configure
```bash
pip install requests termcolor scipy
```

You'll want to take a look at the gcode parameters in the front and customize them for your machine.

## Notes & Future Work
This is just a little proof-of-concept with example code.

It's meant to spur discussion and lower the bar to doing meaningful, data-driven printer development.

There are lots of improvements that make sense: capturing all data (like each error value from a homing sequence), as well as better error handling for longer-running tests.

Feel free to reach out on the Voron or Doomcube Discords if you found this useful, or even add an Issue or PR.