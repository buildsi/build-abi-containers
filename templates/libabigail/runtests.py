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

def create_outdir(filename):
    """Create the output directory for a given filename
    """
    out_dir = os.path.dirname(filename)
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

def run(cmd):
    """
    Run a command with os.system
    """
    if cmd:
        print(cmd)
        os.system(cmd)

def main():
    """
    Entrypoint to run tests.
    """
    package = "{{ package.name }}"
    here = os.getcwd()
    envpath = os.environ["PATH"]

    # Run extra commands first
    lookup = find_install_paths(package)
{% if package.run %}
    for spec, path in lookup.items():

        # If there is a set of commands to run, do it first
        os.chdir(path)
        # Add package bin to the path and run extra commands
        os.environ["PATH"] = "%s/bin:%s" % (os.getcwd(), envpath)
        {% for run in package.run %}run("{{ run }}")
        {% endfor %}
        os.chdir(here){% endif %}

    # spec names -> paths
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
        run("time -p abidw {% for include in package.headers %} --hd %s/{{ include }} {% endfor %} %s --out-file %s/{{ lib }}.xml > %s/{{ lib }}.xml.log 2>&1" % ({% for include in package.headers %}path, {% endfor %}lib, out_dir, out_dir))

        for spec2, path2 in lookup.items():
            spec2, spec2_version = spec2.split("@", 1)
            print("Comparing %s versions %s and %s {{ lib }} with abidiff" %(spec, spec_version, spec2_version))
            out_file = "/results/{{ tester.name }}/{{ tester.version }}/{{ package.name }}/diff/%s-%s" % (spec_version, spec2_version)
            create_outdir(out_file)

            # Only run if the named library exists
            lib2 = "%s/{{ lib }}" % path2
            if not os.path.exists(lib2):
                print("Skipping %s, does not exist.")
                continue

            run("time -p abidiff {% for include in package.headers %} --hd1 %s/{{ include }} --hd2 %s/{{ include }} {% endfor %} %s %s > %s > %s.log" %({% for include in package.headers %}path, path2, {% endfor %}lib, lib2, out_file, out_file))

            # If we have bins to run abicompat with
            {% for binary in package.bins %}
            bin1 = os.path.join(path, "{{ binary }}") 

            # We can only run abicompat if it exists
            if os.path.exists(bin1):

                out_file = "/results/{{ tester.name }}/{{ tester.version }}/{{ package.name }}/compat/%s-%s" % (spec_version, spec2_version)
                create_outdir(out_file)
                
                # Important! This requires debug sumbols, so we allow to fail since most don't have
                run("time -p abicompat %s %s %s > %s > %s.log" % (bin1, lib, lib2, out_file, out_file))
                {% endfor %}
        {% endfor %}


if __name__ == "__main__":
    main()
