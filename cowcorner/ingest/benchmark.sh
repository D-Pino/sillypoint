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
echo "🐌 Running naive approach..."
echo "----------------------------------------"
start_time=$(date +%s.%N)
python naive.py --num-deliveries "$NUM_DELIVERIES"
end_time=$(date +%s.%N)
naive_duration=$(echo "$end_time - $start_time" | bc)
echo "Naive approach completed in: ${naive_duration}s"
echo ""

# Run raw_sql approach
echo "⚡ Running raw_sql approach..."
echo "----------------------------------------"
start_time=$(date +%s.%N)
python raw_sql.py --num-deliveries "$NUM_DELIVERIES" --batch-size "$BATCH_SIZE"
end_time=$(date +%s.%N)
raw_sql_duration=$(echo "$end_time - $start_time" | bc)
echo "Raw SQL approach completed in: ${raw_sql_duration}s"
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
echo "Naive:     ${naive_duration}s"
echo "Raw SQL:   ${raw_sql_duration}s"
echo "Optimized: ${optimized_duration}s"