"""Recount every prior unambiguous identity against the calibrated extension."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from pipeline import body_identity as current


def main():
    source = subprocess.check_output(['git','show','b776851:pipeline/body_identity.py'],cwd=ROOT)
    prior = types.ModuleType('_identity_before_runtime_port')
    sys.modules[prior.__name__] = prior
    exec(compile(source, 'b776851:pipeline/body_identity.py', 'exec'), prior.__dict__)
    catalog = json.loads(current.CATALOG.read_text())
    names = {current.vocab.engine_key(row['name']):row['name'] for row in catalog['cards']}
    checked, regressions, added, ambiguous = 0, [], [], []
    for key, old in prior.tables().items():
        new = current.tables()[key]
        for hp, candidates in old.items():
            if len(candidates) == 1:
                checked += 1
                before = prior.resolve(names[key[0]], hp, key[1])
                after = current.resolve(names[key[0]], hp, key[1])
                if (before.cls,before.form) != (after.cls,after.form):
                    regressions.append([key,hp,before.__dict__,after.__dict__])
                if len(new.get(hp,set())) > 1:
                    ambiguous.append([key,hp,after.__dict__])
        for hp in sorted(new.keys()-old.keys()):
            added.append(dict(parent_form=key,max_hp=hp,identities=sorted(new[hp])))
    result = dict(prior_source_sha256=hashlib.sha256(source).hexdigest(),
        current_source_sha256=hashlib.sha256(Path(current.__file__).read_bytes()).hexdigest(),
        previous_unambiguous_cases=checked,regressions=regressions,added=added,
        ambiguous_retaining_legacy_identity=ambiguous)
    (Path(__file__).parent/'identity_extension_v2.json').write_text(json.dumps(result,indent=2))
    assert not regressions, regressions
    print('IDENTITY_EXTENSION_VERIFIED',checked,'prior identities retained;',len(added),'new maxima')


if __name__ == '__main__': main()
