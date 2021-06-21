#!/usr/bin/env python3

from glob import glob
import subprocess
import pytest
import os
import sys

# This runscript provides functions to run smeagle

single_test = True if "{{ experiment }}" == "single-test" else False
double_test = True if "{{ experiment }}" == "double-test" else False
manual_test = True if "{{ experiment }}" == "manual-test" else False

is_single_test = pytest.mark.skipif(not single_test, reason="Only running single-tests.")
is_double_test = pytest.mark.skipif(not double_test, reason="Only running double-tests.")
is_manual_test = pytest.mark.skipif(not manual_test, reason="Only running manual-tests.")
is_single_double_test = pytest.mark.skipif(not single_test and not double_test, reason="Only running single-tests and double-tests.")


def run_smeagle(package, version, path, libname):
    """
    Run smeagle for a library of interest
    """
    print("Testing %s with smeagle" % libname)

    out_dir = "/results/{{ tester.name }}/{{ tester.version }}/%s/%s" % (package, version)
    lib = os.path.join(path, libname)
    libdir = os.path.dirname(libname)

    # The path to the lib might have an extra directory
    result_dir = os.path.join(out_dir, libdir)
    if not os.path.exists(result_dir):
       os.makedirs(result_dir)

    # Smeagle will generate yaml by default
    run("time -p Smeagle -l %s > %s/%s.yaml" % (lib, out_dir, libname))



# Shared variables
here = os.getcwd()
envpath = os.environ["PATH"]

# Helper Functions


def run_command(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.communicate()[0].decode('utf-8')
    if p.returncode != 0:
        sys.exit("Error finding install packages.")
    return out

def find_install_paths(package):
    """
    Use spack find to get a lookup of install paths
    """
    out = run_command(["spack", "find", "--paths", "--no-groups", package])
    out = [x.strip() for x in out.split('\n') if x.strip()]
    paths = {}
    for line in out:
        spec, path = line.split(" ", 1)
        name, spec_version = spec.strip().split("@", 1)
        # [zlib][1.1.12] = /path/to/install
        paths[spec_version] = path.strip()
    return paths

def create_outdir(filename):
    """Create the output directory for a given filename
    """
    out_dir = os.path.dirname(filename)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

def add_libregex(path, libregex):
    """
    Add library regex
    """
    libs = []
    if libregex:
        os.chdir(path)
        for regex in libregex:
            libs += glob(libregex)
        os.chdir(here)

    # Return unique libs
    return list(set(libs))


def run(cmd):
    """
    Run a command with os.system
    """
    if cmd:
        print(cmd)
        os.system(cmd)


@is_single_test
@pytest.mark.parametrize('package,version,libs,libregex', [{% for package in packages %}{% for version in package.versions %}
    ("{{ package.name }}", "{{ version }}",
    [{% if package.libs %}{% for lib in package.libs %}"{{ lib }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}],
    [{% if packages.libregex %}{% for libregex in packages.libregex %}"{{ libregex }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}]){% if loop.last %}{% else %},{% endif %}{% endfor %}{% endfor %}])

def test_single_package_smeagle_generate(package, version, libs, libregex):
    """
    Smeagle tests to generate yaml
    """
    paths = find_install_paths(package)

    # We can't run a test if the version is not installed (it should be)
    if version not in paths:
        print("Version %s@%s not found, skipping." %(package, version))
        return
    
    # Add any libregex
    path = paths[version]
    libs += add_libregex(path, libregex)

    for libname in libs:
        
        lib = os.path.join(path, libname)

        # Don't continue if the library does not exist
        if not os.path.exists(lib):
            continue
        print("Testing %s@%s %s with smeagle" % (package, version, libname))
        run_smeagle(package, version, path, libname)
