import importlib.util
import json
from pathlib import Path

import pytest

spec=importlib.util.spec_from_file_location('resume_driver',Path(__file__).with_name('resume_verified_chain.py'))
driver=importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


def test_receipt_corruption_cannot_be_skipped(tmp_path):
    result=tmp_path/'result.json';result.write_text('{"value":1}')
    log=tmp_path/'job.out';log.write_text('SUCCESS')
    job=dict(name='job',command=['python','job.py'],expected=['result.json'],marker='SUCCESS')
    receipt=dict(command=job['command'],exit_code=0,marker_matched=True,
        output_sha256=driver.sha(log),outputs={'result.json':driver.sha(result)})
    path=tmp_path/'job.receipt.json';path.write_text(json.dumps(receipt))
    pin=driver.sha(path)
    assert driver.verify_receipt(tmp_path,tmp_path,job,pin)==pin
    result.write_text('{"value":2}')
    with pytest.raises(ValueError,match='Completed result changed'):
        driver.verify_receipt(tmp_path,tmp_path,job,pin)
    result.write_text('{"value":1}')
    log.write_text('SUCCESS changed')
    with pytest.raises(ValueError,match='Output log changed'):
        driver.verify_receipt(tmp_path,tmp_path,job,pin)
    log.write_text('SUCCESS')
    receipt['exit_code']=1;path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='Receipt changed'):
        driver.verify_receipt(tmp_path,tmp_path,job,pin)
    with pytest.raises(ValueError,match='Invalid receipt'):
        driver.verify_receipt(tmp_path,tmp_path,job)
