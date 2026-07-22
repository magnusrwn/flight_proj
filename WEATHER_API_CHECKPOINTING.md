# Simple, resumable weather API collection

## The goal

The input CSV contains one row for every unique airport and date that needs
weather data. Some requests may fail, the script may be stopped, and the free
API limit means the work may need to be split across several runs.

The simplest safe design is:

1. Never modify the input CSV.
2. Send one request at a time.
3. Append a row to the output CSV only after a request succeeds.
4. Treat rows already in the output CSV as completed requests.
5. On the next run, skip completed requests and retry everything else.

The output CSV therefore acts as both the weather dataset and the checkpoint.
No separate queue file, database, or state file is required.

## Why not delete input rows when they enter the queue?

Being placed in a queue only means that a request is scheduled. It does not
mean that the request succeeded.

Consider this sequence:

```text
Delete input row
    -> send request
    -> API returns an error, or the program crashes
```

The input row is now gone, but no weather result was saved. The script no
longer knows that the request needs to be retried.

Deleting a CSV row is also not an efficient operation. A CSV is one continuous
text file, so removing one row normally means reading and rewriting the entire
file. Rewriting it after every API request adds unnecessary work and increases
the chance of leaving a damaged file if the program stops during a write.

## Why the queue can be removed

The queue is useful when many request tasks produce responses concurrently and
a separate writer consumes them. If requests are deliberately sent one at a
time, there is only one response to handle at a time:

```text
send request
    -> await response
    -> write successful response
    -> sleep
    -> repeat
```

The response can therefore be written directly. There is no need to pass it
through an in-memory queue first.

The function may still be declared with `async def`. Awaiting each call inside
a normal `for` loop makes the requests sequential even though the HTTP helper
is asynchronous.

## Identifying one request

Each request is uniquely identified by its airport and date:

```python
def request_key(row: dict[str, str]) -> tuple[str, str]:
    return row["airport_code"], row["fl_date"]
```

For example:

```text
("DFW", "2024-04-18")
```

The output must retain that identity. Include at least these columns in every
successful output row:

```python
FIELDNAMES = [
    "airport_code",
    "requested_date",
    "requested_latitude",
    "requested_longitude",
    "latitude",
    "longitude",
    *[f"daily_{field}" for field in API_DAILY_FIELDS],
]
```

`requested_latitude` and `requested_longitude` are the coordinates sent to the
API. `latitude` and `longitude` are the grid coordinates returned by the API.
They can differ slightly, so the airport code and requested date are the safer
checkpoint key.

## Loading completed requests

At startup, read the keys from the existing output CSV:

```python
completed: set[tuple[str, str]] = set()

if OUTPUT_CSV.exists() and OUTPUT_CSV.stat().st_size > 0:
    with open(OUTPUT_CSV, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        completed = {
            (row["airport_code"], row["requested_date"])
            for row in reader
        }
```

If the output does not exist yet, `completed` remains an empty set and every
input row is pending.

## Selecting pending rows

Filter out input rows whose keys are already in `completed`:

```python
pending_rows = [
    row
    for row in DATA_ROWS
    if request_key(row) not in completed
]
```

Limit one run to a conservative number of requests:

```python
MAX_REQUESTS_PER_RUN = 5_000
rows_this_run = pending_rows[:MAX_REQUESTS_PER_RUN]
```

After a later run starts, it reads the expanded output file and naturally moves
on to the next unfinished rows. There is no need to edit `START_ROW` manually.

## Appending successful results

Open the output in append mode and write the header only when the file is new:

```python
new_file = not OUTPUT_CSV.exists() or OUTPUT_CSV.stat().st_size == 0

with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=FIELDNAMES)

    if new_file:
        writer.writeheader()

    for input_row in rows_this_run:
        response = await request_with_retry(
            build_url(input_row),
            "GET",
        )

        if response.success is None:
            # Nothing is written, so this request remains pending and will be
            # tried again during the next run.
            continue

        output_row = build_output_row(input_row, response.success)
        writer.writerow(output_row)
        file.flush()

        await asyncio.sleep(2)
```

Append mode (`"a"`) preserves previous results. Calling `file.flush()` after a
successful row pushes buffered data to the operating system immediately. If
the process is stopped, the next run can still see the rows already written.

## What happens in each failure case?

| Event | Result |
| --- | --- |
| Request succeeds | Result is appended and skipped on future runs. |
| Request fails after retries | Nothing is appended, so it is retried next run. |
| Script stops before a request | Nothing changed; the request remains pending. |
| Script stops after a successful write | The flushed output row marks it complete. |
| Script is run again | Completed keys are loaded and only pending rows are sent. |

## Final structure

The complete flow stays small:

```text
read immutable input CSV
    -> read completed keys from output CSV
    -> select up to 5,000 pending rows
    -> request one row
    -> on success: append and flush
    -> on failure: leave pending
    -> sleep two seconds
    -> repeat
```

This provides safe retries and automatic resume while keeping the script
appropriate for a one-off data collection task.
