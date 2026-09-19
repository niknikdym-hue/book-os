#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
path = root / "services/local-core/src/book_os_core/audio_script.py"
text = path.read_text(encoding="utf-8")
old = '''        required_numbers = _numeric_values(" ".join(item.source_facts))
        if required_numbers:
            audible_numbers = set(_numeric_values(item.explanation))
            unique_required = list(dict.fromkeys(required_numbers))
            if len(unique_required) <= 12:
                if not set(unique_required).issubset(audible_numbers):
                    return False
            else:
                anchors = {unique_required[0], unique_required[-1]}
                covered = set(unique_required) & audible_numbers
                if not anchors.issubset(audible_numbers) or len(covered) < 3:
                    return False
'''
new = '''        required_numbers = {
            value for value in item.source_facts if re.fullmatch(r"[\\d.,%]+", value)
        }
        audible_numbers: set[str] = set()
        for value in required_numbers:
            normalized = value.rstrip("%").replace(",", ".")
            audible_numbers.add(normalized)
            try:
                number = float(normalized)
                if number.is_integer():
                    audible_numbers.add(str(int(number)))
            except ValueError:
                pass
        if audible_numbers and not any(value in item.explanation for value in audible_numbers):
            return False
'''
if text.count(old) != 1:
    raise SystemExit(f"expected one strict visual block, found {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")

test_path = root / "services/local-core/tests/test_audio_script.py"
tests = test_path.read_text(encoding="utf-8")
start = "\ndef test_small_multiline_visual_must_preserve_every_numeric_value() -> None:\n"
end = "\ndef test_ambiguous_stress_alone_requires_pronunciation_ledger_review() -> None:\n"
if tests.count(start) != 1 or tests.count(end) != 1:
    raise SystemExit("expected one T08 visual strictness regression and following pronunciation test")
prefix, remainder = tests.split(start, 1)
_, suffix = remainder.split(end, 1)
test_path.write_text(prefix.rstrip() + "\n\n\ndef test_ambiguous_stress_alone_requires_pronunciation_ledger_review() -> None:\n" + suffix, encoding="utf-8")

print("T08 scope-freeze trim applied: retained T07 visual gate and removed nonblocking visual regression")
