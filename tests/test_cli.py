"""Integration tests; Python standard library only, all output in a temp folder."""
from pathlib import Path
import math
import re
import subprocess
import sys
import tempfile
import unittest

EXE = str(Path(sys.argv.pop(1)).resolve())


class DemoCLI(unittest.TestCase):
    def run_demo(self, *args, cwd=None):
        return subprocess.run([EXE, *args], cwd=cwd, capture_output=True, timeout=30)

    def test_default_and_threads(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.run_demo(cwd=folder)
            self.assertEqual(result.returncode, 0, result.stderr)
            compute = re.findall(rb"^render computation: ([\d.eE+-]+) seconds$", result.stderr, re.MULTILINE)
            self.assertEqual(len(compute), 1)
            seconds = float(compute[0])
            self.assertTrue(math.isfinite(seconds) and seconds >= 0)
            total = re.search(rb" in ([\d.eE+-]+) seconds", result.stderr)
            self.assertIsNotNone(total)
            self.assertLessEqual(seconds, float(total[1]) + 1e-5)
            data = (Path(folder) / "render.pgm").read_bytes()
            header = b"P5\n160 80\n255\n"
            self.assertTrue(data.startswith(header))
            self.assertEqual(len(data), len(header) + 160 * 80)
            self.assertGreater(max(data[len(header):]), 0)
            for n in (1, 6):
                result = self.run_demo("--width", "31", "--height", "17", "--grid", "8",
                                       "--threads", str(n), "--output", f"{n}.pgm", cwd=folder)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((Path(folder) / "1.pgm").read_bytes(), (Path(folder) / "6.pgm").read_bytes())

    def test_ascii_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            result = self.run_demo("--width", "20", "--height", "10", "--grid", "4", "--ascii", cwd=folder)
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = result.stdout.splitlines()
            self.assertEqual(len(rows), 10)
            self.assertTrue(all(len(row) == 20 for row in rows))

    def test_help_and_errors(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(self.run_demo("--help", cwd=folder).returncode, 0)
            for args in [("--bogus",), ("--width",), ("--width", "1"), ("--height", "-1"),
                         ("--width", "2.5"), ("--grid", "0"), ("--threads", "257"),
                         ("--width", "999999999999999999999999999999999999"),
                         ("--output", "missing/fail.pgm")]:
                with self.subTest(args=args):
                    result = self.run_demo(*args, cwd=folder)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(b"raytracer:", result.stderr)


if __name__ == "__main__":
    unittest.main()
