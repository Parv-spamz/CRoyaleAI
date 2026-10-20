"""Check the first four fixed records using the independent verifier, no predictions."""
import json
from verify_reserved_icebow_corrected import DATA,verify_sources,verify_record

jobs=verify_sources()
with (DATA/'summary.jsonl').open(encoding='utf-8') as stream:
    rows=[json.loads(next(stream)) for _ in range(4)]
assert [r['index'] for r in rows]==list(range(4))
for job,row in zip(jobs,rows):verify_record(job,row)
print('CORRECTED_ICEBOW_INITIAL_FOUR_RECORDS_VERIFIED')
