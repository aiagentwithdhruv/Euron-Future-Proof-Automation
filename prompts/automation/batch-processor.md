---
name: Batch Processor
category: automation
version: 1.0
author: Dhruv
created: 2026-03-15
updated: 2026-03-15
tags: [batch, processing, data, pipeline]
difficulty: intermediate
tools: [claude-code, cursor, gemini]
---

# Batch Processor

## Purpose
> Process files, data, or records in batch with proper error handling, progress tracking, and resumability.

## When to Use
- Processing large datasets or file collections
- Migrating data between systems
- Bulk operations (emails, uploads, transformations)

## The Prompt

```
Build a batch processor for:

**Task:** {{BATCH_TASK}}
**Input:** {{INPUT_SOURCE}}
**Output:** {{OUTPUT_TARGET}}
**Volume:** {{EXPECTED_VOLUME}}

Requirements:
1. Process items in configurable batch sizes
2. Track progress (processed/failed/remaining)
3. Handle individual item failures without stopping the batch
4. Support resuming from where it left off
5. Rate limiting if calling external APIs
6. Generate a summary report at completion
7. Log errors with enough context to debug individual failures

Output:
- Complete processor code
- Configuration (batch size, rate limits, retry count)
- Progress tracking mechanism
- Summary report format
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{BATCH_TASK}}` | What to process | `Resize and optimize product images` |
| `{{INPUT_SOURCE}}` | Where data comes from | `S3 bucket, CSV file, database table` |
| `{{OUTPUT_TARGET}}` | Where results go | `New S3 folder, database, API` |
| `{{EXPECTED_VOLUME}}` | Scale of the job | `~10,000 images, ~5MB each` |
