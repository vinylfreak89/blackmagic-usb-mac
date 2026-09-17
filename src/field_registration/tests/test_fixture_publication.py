#!/usr/bin/env python3
"""Exercise pair recovery without generating 146 MB for each failure case."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import ensure_v9_fixture as fixture


class Publication(unittest.TestCase):
    def test_pair_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generator = root / 'gen_v9_units.py'
            generator.write_text('# fake generator\n')
            raw, csv = (root / ('registration_v9.' + ext) for ext in ('raw', 'csv'))
            stamp = root / '.registration_v9.complete'
            generation = 0

            def generate(args, **kwargs):
                nonlocal generation
                generation += 1
                for option in ('--output', '--truth'):
                    Path(args[args.index(option) + 1]).write_text(str(generation))

            with patch.object(fixture.subprocess, 'run', side_effect=generate):
                fixture.ensure(root)
                fixture.ensure(root)
                self.assertEqual(generation, 1, 'valid pair must not rebuild')
                for missing in (csv, raw, stamp):
                    missing.unlink()
                    fixture.ensure(root)
                    self.assertEqual(raw.read_text(), csv.read_text())
                self.assertEqual(generation, 4)
                # Each stale member separately requires regeneration.
                for stale in (raw, csv):
                    os.utime(stale, ns=(1, 1))
                    fixture.ensure(root)
                    self.assertEqual(raw.read_text(), csv.read_text())
                self.assertEqual(generation, 6)
                stamp.unlink()
                replace = os.replace

                def interrupted(src, dst):
                    replace(src, dst)
                    if Path(dst) == raw:
                        raise InterruptedError('injected interruption after first publication')

                with patch.object(fixture.os, 'replace', side_effect=interrupted):
                    with self.assertRaises(InterruptedError):
                        fixture.ensure(root)
                self.assertFalse(stamp.exists(), 'partial pair must not look committed')
                self.assertNotEqual(raw.read_text(), csv.read_text())
                fixture.ensure(root)
                self.assertTrue(stamp.exists())
                self.assertEqual(raw.read_text(), csv.read_text())
                self.assertEqual(generation, 8)


if __name__ == '__main__':
    unittest.main()
