# Ingestion Pipeline Performance Study

This directory contains an exercise in optimizing data ingestion pipelines using different approaches, demonstrating the performance trade-offs between simplicity, batch processing, and over-optimization.

## Overview

The exercise implements the same cricket delivery ingestion pipeline using three different approaches:

1. **naive.py** - Simple, straightforward approach
2. **optimized.py** - Batch processing with smart database operations  
3. **overengineered.py** - Advanced optimizations with raw SQL

## Approaches

### Naive Approach (`naive.py`)

**Philosophy**: Prioritizes simplicity and readability over performance.

**Key characteristics**:
- Validates and processes deliveries one by one
- Simple, straightforward database operations using ORM
- Each delivery opens a new database session
- Easy to understand and debug
- No batching or bulk operations

**Trade-offs**:
- Extremely readable and maintainable code
- High database overhead due to individual transactions
- Slowest performance but most reliable

### Optimized Approach (`optimized.py`)

**Philosophy**: Balances performance gains with code maintainability.

**Key characteristics**:
- Processes deliveries in configurable batches (default: 1000)
- Validates entire batches at once
- Checks database for existing entities before inserting
- Uses ORM with bulk operations (`add_all`)
- Smart duplicate handling with existence checks

**Trade-offs**:
- Significantly faster than naive approach
- More complex code organization
- Better database efficiency through batching
- Still maintains good readability

**Design decisions**:
- Separates data retrieval, validation, and persistence
- Checks database for existing entities to avoid duplicates
- Prefers "smart" inserts over letting database handle conflicts
- Maintains lookup dictionaries to minimize database queries

### Overengineered Approach (`overengineered.py`)

**Philosophy**: Pursues maximum performance through advanced optimization techniques.

**Key characteristics**:
- Raw SQL with `ON CONFLICT DO NOTHING` clauses
- Bulk operations for all entity types
- Minimal database round trips
- Pre-generated UUIDs to avoid database ID generation
- Advanced data preparation and lookup strategies

**Trade-offs**:
- Most complex implementation
- Uses raw SQL instead of ORM safety
- Surprisingly ended up slower than the optimized approach
- Harder to maintain and debug

**Why it's slower**:
Despite the advanced optimizations, this approach became slower than the "optimized" version due to:
- Overhead from complex data preparation
- Multiple raw SQL statements per batch
- Loss of ORM optimizations
- Premature optimization leading to inefficient patterns

## Performance Results

Based on benchmark testing with the included `benchmark.sh` script:

1. **Naive**: Slowest but most reliable
2. **Optimized**: Best performance-to-maintainability ratio  
3. **Overengineered**: Slower than optimized despite advanced techniques

## Key Learnings

1. **Premature optimization is the root of all evil**: The overengineered approach demonstrates how pursuing theoretical optimizations can lead to worse real-world performance.

2. **Batching provides the biggest wins**: The jump from naive to optimized (introducing batching) provides the most significant performance improvement.

3. **ORM vs Raw SQL**: Modern ORMs like SQLAlchemy are highly optimized and can outperform hand-written SQL when used correctly.

4. **Maintainability matters**: The optimized approach strikes the best balance between performance and code maintainability.

## Usage

Run individual scripts:
```bash
python naive.py --num-deliveries 20000
python optimized.py --num-deliveries 20000 --batch-size 1000  
python overengineered.py --num-deliveries 20000 --batch-size 1000
```

Compare performance:
```bash
./benchmark.sh [num_deliveries] [batch_size]
```

## Files

- `naive.py` - Simple one-by-one processing
- `optimized.py` - Batch processing with ORM
- `overengineered.py` - Advanced optimizations with raw SQL
- `utils.py` - Shared utilities for data loading and validation
- `benchmark.sh` - Performance comparison script
- `README.md` - This documentation