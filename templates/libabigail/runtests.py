#!/usr/bin/env python3

from glob import glob
import subprocess
import pytest
import os
import sys

# This runscript provides functions to run abidw, abicompat, and abidiff. 

# Run tests bases on experiment type
single_test = True if "{{ experiment }}" == "single-test" else False
double_test = True if "{{ experiment }}" == "double-test" else False
manual_test = True if "{{ experiment }}" == "manual-test" else False

is_single_test = pytest.mark.skipif(not single_test, reason="Only running single-tests.")
is_double_test = pytest.mark.skipif(not double_test, reason="Only running double-tests.")
is_manual_test = pytest.mark.skipif(not manual_test, reason="Only running manual-tests.")
is_single_double_test = pytest.mark.skipif(not single_test and not double_test, reason="Only running single-tests and double-tests.")


# Libabigail supporting functions

def run_abidw(path, lib, libname, out_dir, headers):
    """
    Run abidw and create output directory if does not exist.
    """
    print("Testing %s with abidw" % libname)
            
    # Assumes path for spack install
    lib = os.path.join(path, libname)
    libdir = os.path.dirname(libname)
    result_dir = os.path.join(out_dir, libdir)
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)                  

    headers = " ".join(["--hd %s/%s" %(path, header) for header in headers])

    # We don't need output here, lazy way to do it
    run("time -p abidw %s %s --out-file %s/%s.xml > %s/%s.xml.log 2>&1" % (headers, lib, out_dir, libname, out_dir, libname))


def run_abidiff(libname1, libname2, package1, package2, version1, version2, path1, path2, headers1, headers2):
    """
    Run abidiff and create output directory if does not exist.
    """
    print("--- Comparing %s and %s with abidiff" % (libname1, libname2))        

    headers1 = " ".join(["--hd1 %s/%s" %(path1, header) for header in headers1])
    headers2 = " ".join(["--hd2 %s/%s" %(path2, header) for header in headers2])
    out_file = "/results/{{ tester.name }}/{{ tester.version }}/%s/diff/%s/%s-%s" % (package1, package2, version1, version2)
    create_outdir(out_file)

    lib1 = os.path.join(path1, libname1)
    lib2 = os.path.join(path2, libname2)
                    
    if not os.path.exists(lib1) or not os.path.exists(lib2):
        return

    # Assuming we can run for different packages
    run("time -p abidiff %s %s %s %s > %s > %s.log" %(headers1, headers2, lib1, lib2, out_file, out_file))


def run_abicompat(pkg1, pkg2, binary, path, lib1, lib2, version1, version2):
    """
    Run abicompat and create output directory if does not exist.
    """
    binary = os.path.join(path, binary) 

    # We can only run abicompat if it exists
    if os.path.exists(binary):
        out_file = "/results/{{ tester.name }}/{{ tester.version }}/%s/compat/%s/%s-%s" % (pkg1, pkg2, version1, version2)
        create_outdir(out_file)                

        # Important! This requires debug symbols, so we allow to fail since most don't have
        run("time -p abicompat %s %s %s > %s > %s.log" % (binary, lib1, lib2, out_file, out_file))


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
            libs += glob(regex)
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

# Single tests for the same package have the same libs

@is_single_test
@pytest.mark.parametrize('package,version,libs,libregex,headers', [{% for package in packages %}{% for version in package.versions %}
    ("{{ package.name }}", "{{ version }}",
    [{% if package.libs %}{% for lib in package.libs %}"{{ lib }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}],
    [{% if package.libregex %}{% for libregex in package.libregex %}"{{ libregex }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}],
    [{% if package.headers %}{% for header in package.headers %}"{{ header }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}]){% if loop.last %}{% else %},{% endif %}{% endfor %}{% endfor %}])

def test_single_package_abidw(package, version, libs, libregex, headers):
    """
    Libabigail tests for a single package for abidw
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
        
        out_dir = "/results/{{ tester.name }}/{{ tester.version }}/%s/%s" % (package, version)
        lib = os.path.join(path, libname)
        libdir = os.path.dirname(lib)

        # The path to the lib might have an extra directory
        result_dir = os.path.join(out_dir, libdir)
        if not os.path.exists(result_dir):
           os.makedirs(result_dir)

        # Don't continue if the library does not exist
        if not os.path.exists(lib):
            continue
        print("Testing %s@%s %s with abidw" % (package, version, libname))
        run_abidw(path, lib, libname, out_dir, headers) 
        


@is_single_double_test
@pytest.mark.parametrize('pkg1,pkg2,version1,version2,libs1,libs2,regex1,regex2,heads1,heads2', [{% for test in tests %}
    ("{{ test.package1.name }}", "{{ test.package2.name }}", "{{ test.version1 }}", "{{ test.version2 }}",
    [{% if test.package1.libs %}{% for lib in test.package1.libs %}"{{ lib }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}],
    [{% if test.package2.libs %}{% for lib in test.package2.libs %}"{{ lib }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}],
    [{% if test.package1.libregex %}{% for libregex in test.package1.libregex %}"{{ libregex }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}],
    [{% if test.package2.libregex %}{% for libregex in test.package2.libregex %}"{{ libregex }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}],
    [{% if test.package1.headers %}{% for header in test.package1.headers %}"{{ header }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}],
    [{% if test.package2.headers %}{% for header in test.package2.headers %}"{{ header }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}]){% if loop.last %}{% else %},{% endif %}{% endfor %}])

def test_package_abidiff(pkg1, pkg2, version1, version2, libs1, libs2, regex1, regex2, heads1, heads2):
    """
    Libabigail tests for a single or double package running abidiff.
    
    We are either comparing a package to versions of itself, or another.
    """
    paths = {pkg1: find_install_paths(pkg1), pkg2: find_install_paths(pkg2)}
    
    # We can only test versions that exists
    if version1 not in paths[pkg1] or version2 not in paths[pkg2]:
        print("Cannot test abidiff %s@%s vs. %s@%s, install missing." %(pkg1, version1, pkg2, version2))
        return

    
    print("Testing %s@%s vs. %s@%s" %(pkg1, version1, pkg2, version2))
    path1 = paths[pkg1][version1]
    path2 = paths[pkg2][version2]
    libs1 += add_libregex(path1, regex1)
    libs2 += add_libregex(path2, regex2)

    # This could compare even differently named libs.
    for libname1 in libs1:
        for libname2 in libs2:
            run_abidiff(libname1, libname2, pkg1, pkg2, version1, version2, path1, path2, heads1, heads2)



@is_single_double_test
@pytest.mark.parametrize('pkg1,pkg2,version1,version2,libs1,libs2,regex1,regex2,runs1,runs2,bins1,bins2', [{% for test in tests %}
    ("{{ test.package1.name }}", "{{ test.package2.name }}", "{{ test.version1 }}", "{{ test.version2 }}",
    [{% if test.package1.libs %}{% for lib in test.package1.libs %}"{{ lib }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}],
    [{% if test.package2.libs %}{% for lib in test.package2.libs %}"{{ lib }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}],
    [{% if test.package1.libregex %}{% for libregex in test.package1.libregex %}"{{ libregex }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}],
    [{% if test.package2.libregex %}{% for libregex in test.package2.libregex %}"{{ libregex }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}],
    [{% if test.package1.runs %}{% for run in test.package1.runs %}"{{ run }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}],
    [{% if test.package2.runs %}{% for run in test.package2.runs %}"{{ run }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}],
    [{% if test.package1.bins %}{% for binary in test.package1.bins %}"{{ binary }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}],
    [{% if test.package2.bins %}{% for binary in test.package2.bins %}"{{ binary }}"{% if loop.last %}{% else %},{% endif %}{% endfor %}{% endif %}]){% if loop.last %}{% else %},{% endif %}{% endfor %}])

def test_package_abicompat(pkg1, pkg2, version1, version2, libs1, libs2, regex1, regex2, runs1, runs2, bins1, bins2):
    """
    Libabigail tests for a single or double package with abicompat.
    """
    paths = {pkg1: find_install_paths(pkg1), pkg2: find_install_paths(pkg2)}

    # We can only test versions that exists
    if version1 not in paths[pkg1] or version2 not in paths[pkg2]:
        print("Cannot test abicompat for %s@%s vs. %s@%s, install missing." %(pkg1, version1, pkg2, version2))
        return

    print("Testing %s@%s vs. %s@%s" %(pkg1, version1, pkg2, version2))
    path1 = paths[pkg1][version1]
    path2 = paths[pkg2][version2]
    libs1 += add_libregex(path1, regex1)
    libs2 += add_libregex(path2, regex2)

    # If there is a set of commands to run, do it first
    for path, runs in [(path1, runs1), (path2, runs2)]: 
        os.chdir(path)
        # Add package bin to the path and run extra commands
        os.environ["PATH"] = "%s/bin:%s" % (os.getcwd(), envpath)
        for runitem in runs:
            run(runitem)
        os.chdir(here)

    # Testing binaries for first package
    for libname1 in libs1:
        lib1 = os.path.join(path1, libname1)
        for libname2 in libs2:
            lib2 = os.path.join(path2, libname2)
            for binary in bins1:
                run_abicompat(pkg1, pkg2, binary, path1, lib1, lib2, version1, version2)
            for binary in bins2:
                run_abicompat(pkg1, pkg2, binary, path2, lib2, lib1, version1, version2)
