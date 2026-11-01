"""Exercise optional transcripts without USB, network, or the main entry point."""
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]

class StartupDiagnosticsTests(unittest.TestCase):
    def fixture(self, folder, body):
        root = Path(folder)
        (root / 'resources').mkdir()
        shutil.copy2(ROOT / 'resources/diagnostics.sh', root / 'resources/diagnostics.sh')
        script = root / 'fixture.sh'
        script.write_text('''#!/bin/bash
source "$(dirname "$0")/resources/diagnostics.sh"
print() { printf '%s\\n' "$*"; }
input() { printf '[Input] %s\\n' "$*"; }
log() { printf '[Log] %s\\n' "$*"; }
warn() { printf '[WARNING] %s\\n' "$*"; }
cleanup() { echo CLEANUP; }
kit_diagnostics_start
trap 'kit_exit cleanup' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
''' + body)
        return script

    def run_fixture(self, body, answer='y\n', collision=False):
        with tempfile.TemporaryDirectory() as folder:
            script = self.fixture(folder, body)
            if collision:
                (Path(folder) / 'saved').write_text('not a directory')
            result = subprocess.run(['/bin/bash', str(script)], input=answer, text=True,
                                    capture_output=True, timeout=8)
            logs = [p.read_text() for p in (Path(folder) / 'saved/diagnostics').glob('session-*')]
            return result, logs

    def test_enabled_captures_both_streams_flushes_cleanup_and_preserves_failure(self):
        result, logs = self.run_fixture('echo STDOUT\necho STDERR >&2\nexit 27\n')
        self.assertEqual(result.returncode, 27, result.stderr)
        self.assertEqual(len(logs), 1)
        for line in ('STDOUT', 'STDERR', 'CLEANUP', 'Diagnostic log:'):
            self.assertIn(line, logs[0])
        self.assertNotIn('did not close normally', result.stdout)

    def test_declining_creates_no_transcript_and_continues(self):
        result, logs = self.run_fixture('echo WORKFLOW\nexit 0\n', 'n\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('WORKFLOW', result.stdout)
        self.assertEqual(logs, [])

    def test_input_is_preserved_and_keystrokes_are_not_logged(self):
        result, logs = self.run_fixture('IFS= read -r value\n[[ $value == PRIVATE_INPUT ]] || exit 9\necho INPUT_OK\n', 'y\nPRIVATE_INPUT\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('INPUT_OK', logs[0])
        self.assertNotIn('PRIVATE_INPUT', logs[0])

    def test_log_creation_failure_does_not_block_normal_workflow(self):
        result, logs = self.run_fixture('echo WORKFLOW\nexit 0\n', collision=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Continuing without optional logging', result.stdout)
        self.assertIn('WORKFLOW', result.stdout)
        self.assertEqual(logs, [])

    def test_termination_keeps_original_status_and_closes_log(self):
        with tempfile.TemporaryDirectory() as folder:
            script = self.fixture(folder, 'echo READY\nwhile true; do sleep 0.1; done\n')
            proc = subprocess.Popen(['/bin/bash', str(script)], stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                proc.stdin.write('y\n'); proc.stdin.flush()
                deadline = time.monotonic() + 4
                logs = []
                while time.monotonic() < deadline:
                    logs = [p for p in (Path(folder) / 'saved/diagnostics').glob('session-*') if p.is_file()]
                    if logs and 'READY' in logs[0].read_text(): break
                    time.sleep(.02)
                self.assertTrue(logs and 'READY' in logs[0].read_text())
                proc.send_signal(signal.SIGTERM)
                out, err = proc.communicate(timeout=5)
                self.assertEqual(proc.returncode, 143, err)
                self.assertIn('CLEANUP', logs[0].read_text())
                self.assertNotIn('did not close normally', out)
            finally:
                if proc.poll() is None: proc.kill(); proc.communicate()

    def test_prompt_precedes_normal_entry_and_all_exit_cleanup_paths_flush(self):
        source = (ROOT / 'restore.sh').read_text()
        entry = source[source.index('\nfor i in "$@"; do\n'):]
        self.assertLess(entry.index('kit_diagnostics_start'), entry.index('othertmp='))
        self.assertLess(entry.index('kit_diagnostics_start'), entry.index('\nmain\n'))
        for cleanup in ('clean', 'clean_sudo', 'clean_usbmuxd'):
            self.assertIn('trap "kit_exit ' + cleanup + '" EXIT', source)
        self.assertIn('kit_result=$?', entry)
        self.assertIn('exit "$kit_result"', entry)

if __name__ == '__main__': unittest.main()
