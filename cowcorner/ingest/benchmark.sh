#!/bin/bash

# Benchmark script for comparing ingestion approaches
# Usage: ./benchmark.sh [num_deliveries] [batch_size]

set -e

# Default values
NUM_DELIVERIES=${1:-20000}
BATCH_SIZE=${2:-1000}

echo "=== Ingestion Performance Comparison ==="
echo "Testing with $NUM_DELIVERIES deliveries and batch size $BATCH_SIZE"
echo ""

# Change to the ingest directory
cd "$(dirname "$0")"

# Run naive approach
# echo "🐌 Running naive approach..."
# echo "----------------------------------------"
# start_time=$(date +%s.%N)
# python naive.py --num-deliveries "$NUM_DELIVERIES"
# end_time=$(date +%s.%N)
# naive_duration=$(echo "$end_time - $start_time" | bc)
# echo "Naive approach completed in: ${naive_duration}s"
# echo ""

# Run moderate approach
echo "⚡ Running moderate approach..."
echo "----------------------------------------"
start_time=$(date +%s.%N)
python moderate.py --num-deliveries "$NUM_DELIVERIES" --batch-size "$BATCH_SIZE"
end_time=$(date +%s.%N)
moderate_duration=$(echo "$end_time - $start_time" | bc)
echo "Moderate approach completed in: ${moderate_duration}s"
echo ""

# Run optimized approach
echo "🚀 Running optimized approach..."
echo "----------------------------------------"
start_time=$(date +%s.%N)
python optimized.py --num-deliveries "$NUM_DELIVERIES" --batch-size "$BATCH_SIZE"
end_time=$(date +%s.%N)
optimized_duration=$(echo "$end_time - $start_time" | bc)
echo "Optimized approach completed in: ${optimized_duration}s"
echo ""

# # Calculate speedups
# moderate_speedup=$(echo "scale=2; $naive_duration / $moderate_duration" | bc)
# optimized_speedup=$(echo "scale=2; $naive_duration / $optimized_duration" | bc)

echo "=== Results Summary ==="
# echo "Naive:     ${naive_duration}s"
# echo "Moderate:  ${moderate_duration}s (${moderate_speedup}x faster)"
echo "Moderate:  ${moderate_duration}s"
# echo "Optimized: ${optimized_duration}s (${optimized_speedup}x faster)"
echo "Optimized: ${optimized_duration}s"