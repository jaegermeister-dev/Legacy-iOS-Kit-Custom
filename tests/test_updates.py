"""Check updater decisions and rollback using local files, never GitHub/devices."""
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('kit_updates', ROOT/'resources/updater/update.py')
u = importlib.util.module_from_spec(spec); spec.loader.exec_module(u)

class UpdateTests(unittest.TestCase):
    def root(self, directory):
        root = Path(directory); (root/'resources').mkdir()
        (root/'resources/custom-version').write_text('1.0.0\n')
        (root/'resources/update-repository').write_text('fixture/custom-kit\n')
        return root

    def release(self, tag='v1.0.1'):
        prefix = 'https://github.com/fixture/custom-kit/releases/download/' + tag + '/'
        return {'tag_name': tag, 'assets': [dict(name=n, browser_download_url=prefix+n)
            for n in ('Legacy-iOS-Kit-Custom-'+tag[1:]+'.tar.gz', 'SHA256SUMS')]}

    def test_versions_and_publisher_are_checked(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.root(d)
            self.assertIsNone(u.select_release(root, self.release('v1.0.0')))
            self.assertEqual(u.select_release(root, self.release('v1.0.10'))['version'], '1.0.10')
            bad = self.release(); bad['assets'][0]['browser_download_url'] = 'https://example.com/wrong.tar.gz'
            with self.assertRaises(u.UpdateError): u.select_release(root, bad)
            (root/'resources/update-repository').write_text('LukeZGD/Legacy-iOS-Kit')
            with self.assertRaises(u.UpdateError): u.repository(root)

    def test_archive_cannot_replace_saved_files_or_escape_directory(self):
        for name, kind in [('Legacy-iOS-Kit-Custom/saved/keep', 'file'), ('../escape', 'file'),
                           ('Legacy-iOS-Kit-Custom/resources/link', 'symlink')]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as d:
                root = Path(d); archive = root/'bad.tar.gz'; stage = root/'stage'; stage.mkdir()
                with tarfile.open(archive, 'w:gz') as tar:
                    entry = tarfile.TarInfo(name)
                    if kind == 'symlink': entry.type = tarfile.SYMTYPE; entry.linkname = '/tmp/outside'
                    tar.addfile(entry, io.BytesIO(b''))
                with self.assertRaises(u.UpdateError): u.unpack(archive, stage)

    def test_failed_replacement_rolls_back_program_and_preserves_user_data(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.root(d); stage = root/'stage'; stage.mkdir()
            (root/'saved').mkdir(); (root/'saved/ipsw').write_text('USER_DATA')
            (root/'README.md').write_text('old'); (root/'restore.sh').write_text('old launcher')
            (stage/'README.md').write_text('new'); (stage/'restore.sh').write_text('new launcher')
            def fail(source, dest):
                if source == stage/'restore.sh': raise OSError('fixture install failure')
                os.replace(source, dest)
            with self.assertRaises(OSError): u.replace_program(root, stage, rename=fail)
            self.assertEqual((root/'README.md').read_text(), 'old')
            self.assertEqual((root/'restore.sh').read_text(), 'old launcher')
            self.assertEqual((root/'saved/ipsw').read_text(), 'USER_DATA')

    def test_success_keeps_saved_files_and_old_program_backup(self):
        with tempfile.TemporaryDirectory() as d:
            root = self.root(d); stage = root/'stage'; stage.mkdir()
            (root/'saved').mkdir(); (root/'saved/log').write_text('log')
            (root/'restore.sh').write_text('old'); (stage/'restore.sh').write_text('new')
            backup = u.replace_program(root, stage)
            self.assertEqual((root/'restore.sh').read_text(), 'new')
            self.assertEqual((backup/'restore.sh').read_text(), 'old')
            self.assertEqual((root/'saved/log').read_text(), 'log')

    def shell(self, check_code=2, answer=0, install_code=0, skip=False):
        with tempfile.TemporaryDirectory() as d:
            root = self.root(d); (root/'work').mkdir(); fake = root/'python3'
            fake.write_text('''#!/bin/bash
[[ $1 != -c ]] || exit 0
if [[ $2 == check ]]; then echo CHECK; exit CHECK_CODE; fi
echo INSTALL
exit INSTALL_CODE
'''.replace('CHECK_CODE',str(check_code)).replace('INSTALL_CODE',str(install_code)))
            fake.chmod(0o755)
            body = '''source SOURCE
print() { echo "$*"; }
log() { echo "$*"; }
warn() { echo "$*"; }
select_yesno() { return ANSWER; }
no_version_check=SKIP
kit_update_check
result=$?
echo "RESULT:$result"
echo WORKFLOW_AVAILABLE
'''.replace('SOURCE',shlex.quote(str(ROOT/'resources/updater/update.sh'))).replace('ANSWER',str(answer)).replace('SKIP','1' if skip else '0')
            return subprocess.run(['/bin/bash'],input=body,text=True,capture_output=True,
                cwd=root/'work',env={**os.environ,'PATH':str(root)+':'+os.environ['PATH']},timeout=5)

    def test_decline_offline_and_download_failure_never_gate_workflow(self):
        for check, answer, install in [(2,0,0),(1,1,0),(2,1,1)]:
            result = self.shell(check,answer,install)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('RESULT:0',result.stdout)
            self.assertIn('WORKFLOW_AVAILABLE',result.stdout)
            if answer == 0 or check == 1: self.assertNotIn('INSTALL',result.stdout)

    def test_opt_out_never_checks_and_success_requests_relaunch(self):
        result = self.shell(skip=True)
        self.assertNotIn('CHECK',result.stdout); self.assertIn('RESULT:0',result.stdout)
        result = self.shell(answer=1)
        self.assertIn('RESULT:2',result.stdout)
        self.assertIn('Please run the script again',result.stdout)

if __name__ == '__main__': unittest.main()
