#!/usr/bin/env python3
"""Optional release updates. Never access a device or fall back to upstream."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import sys
import tarfile
import tempfile
import urllib.request
import uuid

TOP = {'restore.sh', 'resources', 'bin', 'tests', 'LICENSE', 'README.md',
       'STANDALONE.txt', 'UPSTREAM-README.md', 'RELEASE-NOTES.md',
       '.github', '.gitignore', '.gitattributes'}
PREFIX = 'Legacy-iOS-Kit-Custom'

class UpdateError(Exception): pass

def version(text):
    match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)', text.strip())
    if not match: raise UpdateError('Unrecognised release version')
    return tuple(map(int, match.groups()))

def repository(root):
    name = (root / 'resources/update-repository').read_text().strip()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', name):
        raise UpdateError('No update repository is configured')
    if name.lower() == 'lukezgd/legacy-ios-kit':
        raise UpdateError('The custom updater cannot replace this fork with the official Kit')
    return name

def fetch(url, target=None, limit=4*1024**2):
    request = urllib.request.Request(url, headers={'User-Agent': 'Legacy-iOS-Kit-Custom-Updater',
                                                  'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(request, timeout=25) as response:
        if target is None:
            data = response.read(limit + 1)
            if len(data) > limit: raise UpdateError('Update metadata exceeds its size limit')
            return data
        with target.open('wb') as stream:
            while True:
                block = response.read(1024**2)
                if not block: break
                stream.write(block)

def select_release(root, release):
    repo = repository(root)
    if release.get('draft') or release.get('prerelease'): return None
    tag = release['tag_name']; current = (root/'resources/custom-version').read_text().strip()
    if version(tag) <= version(current): return None
    value = '.'.join(map(str, version(tag)))
    filename = 'Legacy-iOS-Kit-Custom-' + value + '.tar.gz'
    assets = {a['name']: a['browser_download_url'] for a in release.get('assets', [])}
    urls = [assets.get(filename), assets.get('SHA256SUMS')]
    expected = 'https://github.com/' + repo + '/releases/download/' + tag + '/'
    if not all(isinstance(u, str) and u.startswith(expected) for u in urls):
        raise UpdateError('The release does not have the expected archive and checksum assets')
    return dict(repository=repo, tag=tag, version=value, archive=urls[0], checksum=urls[1], filename=filename)

def unpack(archive, stage):
    """Extract only owned program files, never user data or escaping links."""
    seen = set(); total = 0
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar:
            raw = member.name.rstrip('/'); path = PurePosixPath(raw)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] != PREFIX:
                raise UpdateError('Unsafe update archive path')
            parts = path.parts[1:]
            if not parts:
                if member.isdir(): continue
                raise UpdateError('Invalid archive root')
            if parts[0] not in TOP or parts in seen:
                raise UpdateError('Unexpected or duplicate update archive entry')
            seen.add(parts)
            total += member.size
            if total > 2 * 1024**3: raise UpdateError('Unpacked release is too large')
            destination = stage.joinpath(*parts)
            if member.isdir(): destination.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                destination.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as src, destination.open('wb') as dst:
                    shutil.copyfileobj(src, dst)
                destination.chmod(member.mode & 0o777)
            else:
                raise UpdateError('Links and special files are not allowed in update archives')
    for name in ('restore.sh', 'LICENSE', 'resources/custom-version', 'resources/update-repository',
                 'resources/diagnostics.sh', 'resources/updater/update.py'):
        if not (stage/name).is_file(): raise UpdateError('Incomplete release: ' + name)
    for folder in ('bin/macos', 'bin/linux/x86_64', 'bin/linux/arm64'):
        if not (stage/folder).is_dir(): raise UpdateError('Missing host tools: ' + folder)

def replace_program(root, stage, rename=os.replace):
    """Retain user files; keep old program files for recovery and roll back errors."""
    backup = root/'saved/updates'/('previous-' + uuid.uuid4().hex)
    backup.mkdir(parents=True)
    moved = []; installed = []
    try:
        # Replace the launcher last. The current process exits after installation.
        for name in sorted(TOP - {'restore.sh'}) + ['restore.sh']:
            if not (stage/name).exists(): continue
            if (root/name).exists() or (root/name).is_symlink():
                rename(root/name, backup/name); moved.append(name)
            rename(stage/name, root/name); installed.append(name)
    except BaseException:
        for name in reversed(installed):
            rename(root/name, stage/name)
        for name in reversed(moved): rename(backup/name, root/name)
        raise
    return backup

def install(root, plan):
    repo = repository(root)
    if plan.get('repository') != repo: raise UpdateError('Update repository changed; check again')
    # Re-fetch the selected release instead of trusting URLs in a stale local plan.
    version(plan['tag'])
    release = json.loads(fetch('https://api.github.com/repos/' + repo + '/releases/tags/' + plan['tag']))
    checked = select_release(root, release)
    if checked != plan: raise UpdateError('Release changed; check for updates again')
    if (root/'.git').exists():
        raise UpdateError('This is a source checkout. Update it manually to preserve local changes')
    if shutil.disk_usage(root).free < 2 * 1024**3:
        raise UpdateError('At least 2 GiB free disk space is required for an update')
    with tempfile.TemporaryDirectory(prefix='.lik-update-', dir=str(root.parent)) as temporary:
        work = Path(temporary); archive = work/'release.tar.gz'; stage = work/'staged'; stage.mkdir()
        sums = fetch(plan['checksum']).decode('ascii')
        lines = [line.split() for line in sums.splitlines()]
        matches = [row[0] for row in lines if len(row) == 2 and row[1].lstrip('*') == plan['filename']]
        if len(matches) != 1 or not re.fullmatch('[0-9a-fA-F]{64}', matches[0]):
            raise UpdateError('No unique checksum for this release archive')
        print('Downloading custom release ' + plan['version'] + '...', flush=True)
        fetch(plan['archive'], archive)
        h = hashlib.sha256()
        with archive.open('rb') as stream:
            for block in iter(lambda: stream.read(1024**2), b''): h.update(block)
        if h.hexdigest() != matches[0].lower(): raise UpdateError('Release checksum mismatch')
        unpack(archive, stage)
        if (stage/'resources/custom-version').read_text().strip() != plan['version'] or repository(stage) != repo:
            raise UpdateError('Release identity does not match the requested update')
        backup = replace_program(root, stage)
        print('Update installed. Previous program files: ' + str(backup), flush=True)

def main():
    p = argparse.ArgumentParser(); p.add_argument('action', choices=('check','install'))
    p.add_argument('--root', required=True, type=Path); p.add_argument('--plan', required=True, type=Path)
    args = p.parse_args(); root = args.root.resolve()
    try:
        if args.action == 'check':
            release = json.loads(fetch('https://api.github.com/repos/' + repository(root) + '/releases/latest'))
            plan = select_release(root, release)
            if plan is None: print('This custom release is up to date.'); return 0
            args.plan.write_text(json.dumps(plan) + '\n')
            print('A newer custom release is available: ' + plan['version'])
            return 2
        def interrupted(signum, frame): raise UpdateError('Update interrupted')
        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGINT, interrupted)
        install(root, json.loads(args.plan.read_text())); return 0
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError, UpdateError) as error:
        print('Update ' + args.action + ' unavailable: ' + str(error), file=sys.stderr)
        return 1

if __name__ == '__main__': sys.exit(main())
