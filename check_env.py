#!/usr/bin/env python3
"""Read-only, standard-library environment inventory; no benchmark or network."""
import argparse
import datetime
import glob
import hashlib
import importlib.util
import json
import os
import platform
import shutil
import ssl
import subprocess
import sys


def read(path):
    try:
        with open(path) as stream:
            return stream.read().strip()
    except (OSError, UnicodeError) as exc:
        return {"unavailable": str(exc)}


def command(argv):
    if not shutil.which(argv[0]):
        return {"unavailable": "command not installed"}
    try:
        result = subprocess.run(argv, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, universal_newlines=True,
                                timeout=5)
        return {"exit_code": result.returncode, "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip()}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"unavailable": str(exc)}


def cgroups():
    """Resolve controller mounts and retain ancestor limits, including v1/v2."""
    membership = read('/proc/self/cgroup')
    mounts = read('/proc/self/mountinfo')
    report = {"membership": membership, "mountinfo": mounts, "limits": []}
    if not isinstance(membership, str) or not isinstance(mounts, str):
        return report
    for line in membership.splitlines():
        _, controllers, group = line.split(':', 2)
        for entry in mounts.splitlines():
            before, after = entry.split(' - ', 1)
            fields, fs = before.split(), after.split()
            if fs[0] not in ('cgroup', 'cgroup2'):
                continue
            if controllers:
                if fs[0] != 'cgroup' or not set(controllers.split(',')) & set(fs[2].split(',')):
                    continue
            elif fs[0] != 'cgroup2':
                continue
            # mountinfo uses octal escapes for spaces and backslashes.
            def unescape(value):
                for escaped, literal in [('\\040', ' '), ('\\011', '\t'),
                                         ('\\012', '\n'), ('\\134', '\\')]:
                    value = value.replace(escaped, literal)
                return value
            root, mount = unescape(fields[3]), unescape(fields[4])
            if root == '/':
                relative = group.lstrip('/')
            elif group == root or group.startswith(root.rstrip('/') + '/'):
                relative = group[len(root):].lstrip('/')
            else:
                report['limits'].append({"mount": mount, "unresolved_group": group})
                continue
            path = os.path.normpath(os.path.join(mount, relative))
            mount = os.path.normpath(mount)
            if os.path.commonpath([path, mount]) != mount:
                continue
            while True:
                files = {}
                for name in ('cpu.max', 'cpu.stat', 'cpuset.cpus.effective',
                             'cpuset.cpus', 'cpu.cfs_quota_us', 'cpu.cfs_period_us',
                             'memory.max', 'memory.limit_in_bytes'):
                    filename = os.path.join(path, name)
                    if os.path.isfile(filename):
                        files[name] = read(filename)
                report['limits'].append({"path": path, "files": files})
                if path == mount:
                    break
                path = os.path.dirname(path)
    return report


def collect():
    try:
        affinity = sorted(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        affinity = None
    packages = {}
    for name in ('Crypto', 'Cryptodome', 'cryptography'):
        try:
            spec = importlib.util.find_spec(name)
            packages[name] = spec.origin if spec else None
        except (ImportError, ValueError) as exc:
            packages[name] = {"unavailable": str(exc)}
    try:
        import _hashlib
        backend = getattr(_hashlib, 'OPENSSL_VERSION', None)
        pbkdf_backend = getattr(getattr(hashlib, 'pbkdf2_hmac', None), '__module__', None)
    except ImportError:
        backend, pbkdf_backend = None, None
    return {
        "schema_version": 1,
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "system": platform.platform(), "architecture": platform.machine(),
        "os_release": read('/etc/os-release'),
        "python": sys.version, "python_executable": sys.executable,
        "ssl_openssl": ssl.OPENSSL_VERSION, "hashlib_openssl_if_exposed": backend,
        "pbkdf2_hmac_available": hasattr(hashlib, 'pbkdf2_hmac'),
        "pbkdf2_backend_module": pbkdf_backend,
        "optional_package_locations_no_import": packages,
        "visible_logical_cpus": os.cpu_count(), "affinity_cpu_ids": affinity,
        "cpu_inventory": command(['lscpu']),
        "memory": read('/proc/meminfo'), "cgroups": cgroups(),
        "openssl_cli": command(['openssl', 'version', '-a']),
        "pci_inventory": command(['lspci', '-nn']),
        "gpu_devices": sorted(glob.glob('/dev/nvidia*') + glob.glob('/dev/dri/*')
                              + glob.glob('/dev/kfd')),
        "nvidia_inventory": command(['nvidia-smi', '--query-gpu=name,driver_version,memory.total',
                                     '--format=csv,noheader']),
        "runtime_library_inventory": command(['ldconfig', '-p']),
        "opencl_icd_files": {p: read(p) for p in glob.glob('/etc/OpenCL/vendors/*.icd')},
        "available_tools": {name: shutil.which(name) for name in
                            ('nvidia-smi', 'clinfo', 'rocminfo', 'nvcc', 'gcc', 'cc', 'hashcat')},
        "limitations": ["Inventory does not prove GPU compute access or runtime compatibility.",
                        "Cgroup namespaces may hide ancestor quotas; unresolved limits need review.",
                        "Optional crypto packages are located without importing or querying versions."]
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='new JSON file in your writable directory')
    args = parser.parse_args()
    report = collect()
    # Exclusive creation protects an existing report from accidental replacement.
    with open(args.output, 'x') as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    print('Saved environment inventory to ' + args.output)


if __name__ == '__main__':
    main()
