"""Check standalone startup and menus without USB, host-service, or network access."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_ios10_jailbreak_option import ROOT, SOURCE, function


class StandaloneTests(unittest.TestCase):
    def run_shell(self, body, *, shallow=False, metadata=True):
        names = ("print", "input", "log", "warn", "error", "version_get",
                 "menu_print_info", "menu_miscutilities", "exit_message", "main")
        script = "\n".join(function(name) for name in names) + r'''
git() { echo UNEXPECTED_GIT >&2; exit 93; }
curl() { echo UNEXPECTED_NETWORK >&2; exit 94; }
download_from_url() { echo UNEXPECTED_NETWORK >&2; exit 94; }
select_yesno() { echo UNEXPECTED_PROMPT >&2; exit 95; }
kit_update_check() { :; }
set_tool_paths() { platform=fixture; platform_ver=fixture; }
device_get_info() { echo DEVICE_LOOKUP; }
device_manufacturing() { :; }
install_depends() { echo UNEXPECTED_INSTALL >&2; exit 96; }
debug_mode=1
device_type=iPhone5,3
device_proc=6
device_mode=none
device_argmode=none
device_latest_vers=10.3.3
unzip2=fixture
zip2=fixture
''' + body
        with tempfile.TemporaryDirectory(prefix="custom-kit-") as directory:
            root = Path(directory)
            (root / "tmp-test").mkdir()
            (root / "resources").mkdir()
            (root / "saved").mkdir()
            (root / "saved/firstrun").write_text("fixture\n")
            if metadata:
                for name in ("custom-version", "upstream-commit"):
                    shutil.copy2(ROOT / "resources" / name, root / "resources" / name)
            if shallow:
                (root / ".git").mkdir()
                (root / ".git/shallow").write_text("old-checkout\n")
                # Old thin-distribution state must not reactivate an updater.
                (root / "resources/new").touch()
            result = subprocess.run(
                [os.environ.get("TEST_BASH", "/bin/bash"), "--noprofile", "--norc"],
                input=script, text=True, capture_output=True, cwd=root / "tmp-test",
                env={"PATH": os.environ["PATH"], "LC_ALL": "C"}, timeout=10,
            )
        self.assertNotIn("UNEXPECTED_", result.stderr)
        self.assertNotIn("command not found", result.stderr)
        return result

    def test_version_is_local_with_or_without_git(self):
        for shallow in (False, True):
            with self.subTest(shallow=shallow):
                result = self.run_shell('version_get\nexit_message\n', shallow=shallow)
                self.assertEqual(result.returncode, 0, result.stderr)
                version = (ROOT / "resources/custom-version").read_text().strip()
                upstream = (ROOT / "resources/upstream-commit").read_text().strip()[:7]
                self.assertIn(version + " (upstream " + upstream + ")", result.stdout)
                self.assertNotIn("update", result.stdout.lower())

    def test_missing_metadata_reports_local_packaging_error(self):
        result = self.run_shell('version_get\n', metadata=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Custom build version files are missing", result.stdout)
        self.assertNotIn("GitHub", result.stdout)

    def test_startup_reaches_device_lookup_without_update_gate(self):
        result = self.run_shell(r'''
no_internet_check=1
run_as_root=1
main_argmode=fixture-no-operation
main
echo STARTUP_COMPLETE
''', shallow=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DEVICE_LOOKUP", result.stdout)
        self.assertIn("STARTUP_COMPLETE", result.stdout)

    def test_failed_internet_probe_does_not_block_local_functionality(self):
        result = self.run_shell(r'''
ping() { return 1; }
run_as_root=1
main_argmode=fixture-no-operation
main
echo STARTUP_COMPLETE
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("startup internet check failed", result.stdout)
        self.assertIn("Online features remain enabled", result.stdout)
        self.assertIn("DEVICE_LOOKUP", result.stdout)
        self.assertIn("STARTUP_COMPLETE", result.stdout)

    def test_legacy_update_state_cannot_nag_in_menus(self):
        result = self.run_shell(r'''
version_get
no_version_check=1
git_hash_latest=different
version_latest=v99.99.99
menu_print_info
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Legacy iOS Kit (Custom)", result.stdout)
        self.assertNotIn("WARNING", result.stdout)
        self.assertNotIn("remote", result.stdout)

    def test_utilities_keep_tools_but_cannot_switch_upstream_branch(self):
        result = self.run_shell(r'''
select_option() {
    local i=0 chosen item
    for item in "$@"; do
        printf 'OPTION:%s\n' "$item"
        [[ $item == "Go Back" ]] && chosen=$i
        ((i+=1))
    done
    return "$chosen"
}
menu_miscutilities
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OPTION:Create Custom IPSW", result.stdout)
        self.assertIn("OPTION:(Re-)Install Dependencies", result.stdout)
        self.assertNotIn("Switch to", result.stdout)

    def test_self_replacement_code_and_endpoints_are_absent(self):
        for removed in ("version_update_check", "version_update()", "version_check()",
                        "git fetch --unshallow", "git pull origin", "git fetch origin",
                        "api.github.com/repos/LukeZGD/Legacy-iOS-Kit",
                        "Do you want to update now?"):
            self.assertFalse(removed in SOURCE, "Self-updater reference remains: " + removed)


if __name__ == "__main__":
    unittest.main()
