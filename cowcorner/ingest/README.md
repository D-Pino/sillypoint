# Ingestion Pipeline Performance Working Exercise

This directory just outlines a simple exercise I undertook to get some better hands-on experience understanding the tradeoffs when trying to optimize a data ingestion pipeline.

## Overview

The exercise implements the same ingestion pipeline using three different approaches:

1. **naive.py** - Simplest possible approach
2. **optimized.py** - Batch processing with smarter database operations  
3. **raw_sql.py** - Skipping the ORM helpers, and writing the raw SQL to actually execute against the db

## Approaches

### Naive Approach (`naive.py`)

Ingest every delivery one-by-one, using simple get_or_create functions to add entities to the db if necessary. Very simple, easy-to-follow, and maintainable, but very slow too.


### Optimized Approach (`optimized.py`)

A more nominal approach to data ingestion. Ingest deliveries in batches. Takes advantage of batch validation using pydantic's TypeAdapter, and also batches db operations to seriously reduce the number of db calls (which in a real scenario due to network latency is even more important than here). A little less simple than the naive version, but much quicker.

### Write-your-own-SQL Approach (`raw_sql.py`)

Still do everything in batches (including validation), but instead of using ORM insert functions, write the raw SQL to execute against the db. In theory, getting lower-level gives you the _opportunity_ to be more optimal. In practice (for this case at least), the ORM is very good, and doing the SQL myself actually made it slower. In addition, it ends up more complex, so harder to read, debug, and maintain.
