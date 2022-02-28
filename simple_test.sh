#!/usr/bin/env bash

mkdir -p x0
./run_test.py double-dragon.local \
  --test_type probe_accuracy \
  --iterations 2 \
  --stats \
  --output \
  --output_path x0/probe_sample_test.json