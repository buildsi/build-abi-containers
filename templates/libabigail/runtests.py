#!/usr/bin/env python3

import subprocess
import os
import sys

# This runscript will run abidw, abicompat, and abidiff. We can't get the original source
# examples so we are skipping looking at those for now. We will need to have a way to
# include them.

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
        paths[spec.strip()] = path.strip()
    return paths


def run(cmd):
    """
    Run a command with os.system
    """
    print(cmd)
    os.system(cmd)


def main():
    """
    Entrypoint to run tests.
    """
    package = "{{ package.name }}"

    # spec names -> paths
    lookup = find_install_paths(package)
    for spec, path in lookup.items():
        spec, spec_version = spec.split("@", 1)
        {% for lib in package.libs %}print("Testing {{ lib }} with abidw")
        out_dir = "/results/{{ tester.name }}/{{ tester.version }}/{{ package.name }}/%s" % spec_version

        # Assumes path for spack install
        libdir = os.path.dirname("{{ lib }}")
        result_dir = os.path.join(out_dir, libdir)
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)

        # Don't run if the library does not exist
        lib = "%s/{{ lib }}" % path
        if not os.path.exists(lib):
            print("Skipping %s, does not exist." % lib)
            continue
            
        # We don't need output here, lazy way to do it
        run("time -p abidw {% for include in package.include %} --hd %s/{{ include }} {% endfor %} %s --out-file %s/{{ lib }}.xml > %s/{{ lib }}.xml.log 2>&1" % ({% for include in package.include %}path, {% endfor %}lib, out_dir, out_dir))

        for spec2, path2 in lookup.items():
            spec2, spec2_version = spec2.split("@", 1)
            print("Comparing %s versions %s and %s {{ lib }} with abidiff" %(spec, spec_version, spec2_version))
            out_file = "/results/{{ tester.name }}/{{ tester.version }}/{{ package.name }}/diff/%s-%s" % (spec_version, spec2_version)
            out_dir = os.path.dirname(out_file)
            if not os.path.exists(out_dir):
                os.mkdir(out_dir)
 
            # Only run if the named library exists
            lib2 = "%s/{{ lib }}" % path2
            if not os.path.exists(lib2):
                print("Skipping %s, does not exist.")
                continue

            run("time -p abidiff {% for include in package.include %} --hd1 %s/{{ include }} --hd2 %s/{{ include }} {% endfor %} %s %s > %s > %s.log" %({% for include in package.include %}path, path2, {% endfor %}lib, lib2, out_file, out_file))
        {% endfor %}


if __name__ == "__main__":
    main()
