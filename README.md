# Build ABI Containers

The goal of this repository is to provide container environments for
evaluating ABI, and to run tests for ABI in the CI. The approach we take is the following:

 - provide base containers with tools to test abi.
 - For some number of packages, [define libraries and binaries](tests) within to build and test.
 - Build a testing container on top of a base container, with multiple versions of a package defined in any given [test](tests)
 - Run the entrypoint of the container with a local volume to run tests and generate output.
 - Tester container bases along with the tester+test are deployed automatically to reproduce running the tests. Testers and bases are built and deployer when a changed tester Dockerfile or file in [tests](tests) is pushed to main.
 - Artifact results are discovered and saved to [build-abi-containers-reuslts](https://github.com/buildsi/build-abi-containers-results).


## Table of Contents

 - [Quick Start](#quick-start)
 - [Concepts](#concepts)
 - [Overview of Steps](#overview-of-steps)
 - [Experiments](#experiments)
 - [Questions for Discussion](#questions-for-discussion)
 - [Organization](#organization)
 - [Usage](#usage)
   - [Build](#build)
   - [Test](#test)
   - [Add a Tester](#add-a-tester)
   - [Add a Package](#add-a-package)
   - [Add a Test](#add-a-test)
   - [Reproduce a Test](#reproduce-a-test)
   - [Bolos Notes](#bolos-notes)

## Quick Start

```bash
# Install dependencies
$ pip install -r requirements.txt

# Build a testing container for a tester and a package (mpich.yaml in tests)
./build-si-containers build mpich

# The default tester is libabigail (the command above is equivalent to):
./build-si-containers build --tester libabigail mpich

# Build and run libabigail's tests
./build-si-containers test mpich

# Deploy the libabgail + mpich tester container
./build-si-containers deploy mpich
```

These commands will be explained in detail in these docs.

## Concepts

### Packages

A package is a spack package, meaning it has versions and variants.
Packages are defined in [packages](packages). Each is a yaml file that can
express libraries built, directories to include, and custom examples to compile.

### Tests

A test is defined by a yaml file in [tests](tests). Specifically, a test can follow
any of the following experiment patterns:

 - Within package experiment, `single-test`
 - Automated between package experiment, `pairwise-test`
 - Hard coded between package experiment `manual-test`

For example, to compare all versions of zlib to one another, we might have:

```yaml
packages:
 # no versions specified implies all
 - name: zlib

# This can be single-test, double-test, or manual-test
# pair-wise test implies we require 2 packages 
experiment:
  name: single-test
```

In the above, since we didn't specify a list of versions, all versions will
be used. The `single-test` directive instructs the framework to generate
tests to compare versions for a single library.

### Tester

A tester is built into a base container image, and intended to run one or more
tests. E.g., libabigail, Smeagle, and Symbolator are testers. Each can build it's
own base container to add packages and specific experiments to.

### Experiment

An experiment is a type of test. Each test file should define one experiment
type by name and relevant packages and metadata. The tester can choose
how to run each experiment type (e.g., two types might share a test).


## Overview of Steps

1. We start with base containers that have "testers" such as libabigail. Their recipe files are included in [docker](docker) and the GitHub workflow [build-deploy.yaml](.github/workflows/build-deploy.yaml). When any of these Dockerfiles change, the bases are built in a pull request (PR), and when the PR is merged the containers are deployed. For example, [here](https://quay.io/repository/buildsi/libabigail?tab=tags) is the libabigail testing base on Quay.io. A tester like libabigail has it's own entrypoint and runscript where we can express how to write tests. For example, libabigail is going to run abidw, abidiff, etc.
2. We define packages to test in [packages](packages) as yaml files. The yaml files include things like header files, versions, and libraries.
3. We define tests for specific packages in [tests](tests). A test can follow a specific experiment type, which will determine the subsets of actual functions that are run in a tester.
4. The package, test metadata (and experiment) are combined and then rendered into the testing template. This means the resulting container of the libabigail base + the package (e.g., mpich) will have a custom runscript to run the libabigail commands on the various libaries, etc.
5. The results are saved in the container at /results, in a tree that will ensure that different tester and package bases have a unique namespace. The tests are run in a GitHub workflow and currently saved as artifacts. (E.g., see [this run](https://github.com/spack/build-abi-containers/actions/runs/882797815)). The artifacts are discovered and saved in [build-abi-containers-results](https://github.com/buildsi/build-abi-containers-results).

It's recommended to read the [usage section](#usage) to get more detail on the above.

## Experiments

The following experiments are valid. 

 - *single-test*: is considered to be testing within a package. E.g., running abidw or testing versions between one another.
 - *double-test*: is testing two different packages together, typically all versions.
 - *manual-test*: is explicitly defining the tests.
 
We will add more experiment types if this set is not appropriate for our use case.
It is up to the tester to decide what to run based on each experiment name. For example,
the libabigail test runscript uses pytest with parameterization, and only runs a subset
of the functions depending on the experiment type.

## Questions for Discussion / Remaining to do

1. Smeagle needs to be finished and added as a tester.
1. We need to derive a means to compare results across different testers. E.g., libabigail vs. Smeagle.

## Organization

 - [docker](docker): includes `Dockerfile`s, one per testing base, that will be deployed to [quay.io/buildsi](https://quay.io/organization/buildsi).
 - [packages](packages): are packages that are defined to test, including versions, libraries, etc..
 - [tests](tests): includes yaml config files that are matched to one or more spack packages and an experiment.
 - [testers](testers): is a folder of tester subdirectories, which should be named for the tester (e.g., libabigail). No other files should be put in this folder root.
 - [templates](templates): includes both container build templates, and tester runtime templates. The container build defaults to Dockerfile.default to build from spack source, and when we have a buildcache (ideally with debug) we can change that to Dockerfile.buildcache (the `--use-cache` argument described next.)

All configs for the above are validated when loaded.

## Usage

The client exposes two commands - to build and run tests. You can see these commands
in use in the [GitHub workflow](.github/workflows/build-deploy.yaml) or continue reading
for details.


```bash
usage: build-si-containers [-h] {test,build} ...

Build SI Container Tester

optional arguments:
  -h, --help    show this help message and exit

actions:
  actions for testing containers for the BUILD SI project

  {test,build}  run-tests actions
    test        run tests.
    build       build a testing container.
```

Test will also do a build, and then run tests for the container.

### Build

#### 0. Install dependencies

Make sure you have the dependencies installed.

```bash
$ pip install -r requirements.txt
```

#### 1. Build a container

The first thing you likely want to do is build your testing container. 
The build command let's you choose a root (the repository here that has a tests and
testers folder), a tester name (we only have one now so it defaults to libabigail),
and if we should use the spack build cache to install (not recommended currently as
it doesn't have most of what we need)

```bash
usage: build-si-containers build [-h] [--use-cache] [--prebuilt] [--cache-only] [--docker-no-cache] [--fail-fast] [--root ROOT]
                                 [--tester {libabigail,all}]
                                 packages [packages ...]

positional arguments:
  packages              packages to test

optional arguments:
  -h, --help            show this help message and exit
  --use-cache           Install from build cache instead of autamus.
  --prebuilt            Use a prebuilt container from ghcr.io/autamus/builds-<package>
  --cache-only          ONLY allow install from build cache.
  --docker-no-cache     Do not use the docker cache.
  --fail-fast           If a container build fails, exit.
  --root ROOT, -r ROOT  The root with the tests and testers directories.
  --tester {libabigail,all}, -t {libabigail,all}
                        The tester to run tests for.
```

We will be doing a multi-stage build with a testing base from [quay.io/buildsi](https://quay.io/organization/buildsi).
If you use a prebuilt container (flag `--prebuilt`) then it needs to be available from [autamus](https://autamus.io) with the
name `ghcr.io/autamus/buildsi-<package>` and have all versions of interest installed. Currently,
the default is to read versions from [tests](tests) and then built from scratch. If you want to build
a test container (e.g., the file mpich.yaml) you can do:

```bash
./build-si-containers build mpich
```

This build is also done for `build-si-containers test` if the container has not
been built yet. During CI, when the container is built and tested, if the label `deploy-test-conatainer`
is applied, the testing container will be pushed to quay.io, where anyone can
pull to rerun and reproduce results. If you want to give the build cache a shot
(maybe if we can update it to include more packages?) you can do:

```bash
./build-si-containers build --use-cache mpich
```

You can say to _only_ use the build cache (packages that aren't completely there
will not be able to build):

```bash
# use the spack build cache, but disable docker cache
./build-si-containers build --use-cache --cache-only mpich
```

This is not recommended unless you have a fully populated cache.
You can also disable using the docker cache, if apppropriate:

```bash
# use the spack build cache, but disable docker cache
./build-si-containers build --use-cache --docker-no-cache mpich
```

All of these cache commands also work for test, since test can also
do a build if necessary.

### Test

Once your container is built, testing is just running it!

```bash
$ docker run -it quay.io/buildsi/libabigail-test-mpich:latest
```

For now, we are building from source, because we do not have a build cache
that is well populated, nor do we have a global debug (this is problematic regardless).
We will need to add global debug to add to these builds for most of the results to be
meaningful. You can also request build and tests to be run at the same time:

```bash
./build-si-containers test mpich
```

The test command also supports a few other parameters:

```bash
usage: build-si-containers test [-h] [--outdir OUTDIR] [--rebuild] [--use-cache] [--prebuilt] [--cache-only] [--docker-no-cache]
                                [--fail-fast] [--root ROOT] [--tester {libabigail,all}]
                                packages [packages ...]

positional arguments:
  packages              packages to test

optional arguments:
  -h, --help            show this help message and exit
  --outdir OUTDIR, -o OUTDIR
                        Write test results to this directory (defaults to results in $PWD)
  --rebuild             Force rebuild of the container if it does not exist.
  --use-cache           Install from build cache instead of autamus.
  --prebuilt            Use a prebuilt container from ghcr.io/autamus/builds-<package>
  --cache-only          ONLY allow install from build cache.
  --docker-no-cache     Do not use the docker cache.
  --fail-fast           If a container build fails, exit.
  --root ROOT, -r ROOT  The root with the tests and testers directories.
  --tester {libabigail,all}, -t {libabigail,all}
                        The tester to run tests for.
```


While the build command will always do a build, the test command will first
look to see if the container already has been built, and not rebuild it if
this is the case. To force a rebuild:

```
./build-si-containers test --rebuild mpich
```

By default, results are saved to the present working directory in a "results"
folder. The structure of the folder is done so that results from different
packages or testers will not overwrite one another. To specify a different folder,
you can do:

```bash
mkdir -p /tmp/tests
./build-si-containers test --outdir /tmp/tests mpich
```

To be safe, the directory must already exist.
You'll see a bunch of commands printed to the screen for the tester.
Running the container will generate results within the container. if you want
to save files generated locally, you need to bind to `/results` in the container.

```bash
$ mkdir -p results
$ docker run -v $PWD/results:/results -it quay.io/buildsi/libabigail-test-mpich:latest
$ tree results/
results/
└── libabigail
    └── 1.8.2
        └── mpich
            ├── 3.0.4
            │   └── lib
            │       ├── libmpich.so.xml
            │       └── libmpich.so.xml.log
...
            ├── 3.4.1
            │   └── lib
            │       ├── libmpich.so.xml
            │       └── libmpich.so.xml.log
            └── diff
                ├── 3.0.4-3.0.4
                ├── 3.0.4-3.0.4.log
                ├── 3.0.4-3.1.4
...
                ├── 3.3.2-3.4.1.log
                ├── 3.4.1-3.0.4
                └── 3.4.1-3.0.4.log
```

We will want to run this in some CI, and upload results to save somewhere (this is not
done yet).

### Deploy

After a container is built, you can use deploy to push to Quay.io.

```bash
./build-si-containers deploy -h
usage: build-si-containers deploy [-h] [--root ROOT] [--tester {libabigail,all}] packages [packages ...]

positional arguments:
  packages              packages to test

optional arguments:
  -h, --help            show this help message and exit
  --root ROOT, -r ROOT  The root with the tests and testers directories.
  --tester {libabigail,all}, -t {libabigail,all}
                        The tester to run tests for.
```

```bash
./build-si-containers deploy mpich
```


### Add a Tester

A tester is a base for running some kind of test on a binary. When you add a tester
you need to:

 1. Give the tester a name (e.g., libabigail) to use across files.
 2. Create the tester's config file and versions
 3. Create the tester runscript (and additional scripts)
 4. Create a Dockerfile base template in [docker](docker) in a subdirectory named for the tester.
 5. Create a Dockerfile test template in [templates](templates) also in a subfolder named for the tester.
 6. Understand how the tester bases are built automatically.
 
Each of these steps will be discussed in detail.
 
#### 1. Give the tester a name

You should choose a simple, lowercase name to identify your tester, and this will
be used for the subfolders and identifiers of the tester.

#### 2. Create the tester config file and versions

You should define your versions to build for a tester in a "versions" file
located in the tester subfolder. For example:

```bash
testers/
└── libabigail
    ├── bin
    │   └── abi-decode
    ├── versions
    └── tester.yaml
```

In the above, we see that a tester also needs a tester.yaml file. This file
defines metadata like the name of the tester (matching the folder), the 
entrypoint and runscript for the container (written to `/build-si/`) along
with the active version. Since we typically want to consistently test using one
version, for now it is designed in this way. So you should write
a config file named `tester.yaml` in the [testers](testers) directory in a subfolder
named for the tester. For example, libabigail looks like:

```yaml
tester:
  name: libabigail
  version: 1.8.2
  runscript: runtests.sh
  entrypoint: /bin/bash
```

Notice the bin folder? Any files that you add in bin will be added to /usr/local/bin, the idea being
you can write extra scripts for the tester to use. For now we are just supporting one version of a tester.

#### 3. Create the tester runscript

See in the above the filename "runtests.sh"? This needs to be found in the templates
folder in the tester directory:

```bash
templates/
├── Dockerfile.default
└── libabigail
    └── runtests.sh
```

It should accept a package object, a tester object, and a version,
and write results to be organized at /results as follows:

```bash
/results/{{ tester name }}/{{ tester version }}/{{ package name }}/{{ package version }}
```

The results will likely need to be parsed to put them into some cohesive format,
when we know what we want.

#### 4. Create Dockerfile base template

The Dockerfile base templates are in [docker](docker), in subfolders named for
the testers. These bases will be built automatically on any changes to the files,
and deployed to [quay.io/buildsi](https://quay.io/organization/buildsi). The purpose
of these containers is to provide a base that has the testing software, onto which
we can install a package and run tests. This means that to add a new testing base you should:

1. Create a subdirectory that matches the name of the tester, e.g [docker/libabigail](docker/libabigail)
2. Create a Dockerfile in this folder with an ubuntu 18.04 or 20.04 base that installs the testing framework. The executables that the tester needs should be on the path. The Dockerfile should accept a `LIBRARY_VERSION` build argument that will set one or more versions to build. You don't need to worry about an `ENTRYPOINT`, as it will be set on the build of the package testing container. You should also install `curl` for spack.

#### 5. Create Dockerfile test template

The Dockerfile test template is optional, and will be used to generate
a multi-stage build for a given package, package version, and tester.
If you don't create a package build template, the default will be used, [templates/Dockerfile.default](templates/Dockerfile.default). If you do create a template,
it can use the following variables:

* package.name: The name of the package to install (e.g., mpich)
* version: The version of the package to install
* tester.name: The name of the tester (e.g., libabigail)
* tester.version: The version of the tester

The entrypoint will be added dynamically based on the tester.entrypoint, and tester.runscript.
We are also suggesting the convention of storing the script in the `build-si` directory
at the root of the container.

#### 6. Understand how the tester bases are built automatically

In [build-deploy.yaml](.github/workflows/build-deploy.yaml) we discover a list of testers by 
way of looking for changed files in the [testers](testers) directory.
Then, for each changed file, we trigger a new build. Versions
for one or more of these builds are derived from the `versions` text file we created earlier.
And that's it! When a file is changed in one of these folders, it will be built during the
pull request process, and deployed on merge to main.


These are the bases we add packages on top of, and then run tests.


### Add a Package

#### Add an Existing Spack Package
Adding an existing package comes down to adding a yaml file in the [packages](packages) 
folder named according to the package (or group) to test.

#### Add an Custom Spack Package

If you want to write a custom package, you can simply create another subfolder in
[spack/packages](spack/packages), which is a test repository of packages
just for the build here. I (@vsoch) found it easiest to put my testing
code for such a package in [its own repository](https://github.com/buildsi/build-abi-test-mathclient)
and then be able to easily install from GitHub releases.

#### Package Metadata

Each package file should include metadata about the package, including
versions, libraries, and extra commands to run.
For example, here is the package file for mpich.

```yaml
package:
 name: mpich
 versions:
  - "3.4.1"
  - "3.3.2"
  - "3.1.4 device=ch3 netmod=tcp"
  - "3.0.4 device=ch3 netmod=tcp"
 headers:
  - include
 libs:
  - lib/libmpich.so

 # Extra commands to run to compile examples.
 # Assumes package bin on the path, relative paths to install directory
 run:
   - mpicc -c share/mpich/src/examples/cpi.c -o share/mpich/src/examples/cpi

 # Binaries to run tests with across versions (relative to install directory)
 bins:
   - share/mpich/src/examples/cpi

test:
  # Always use the build cache instead of prebuilt container?
  build_cache: false
```

A package file can be used for one or more tests, discussed next.

### Add a Test

A test is a yaml file in [tests](tests.yaml). It should typically specify
one package for a `single-test` experiment, and two for a `double-test` or
`manual-test`. For example, here is a `single-test` experiment for zlib:

```yaml
packages:
 # no versions specified implies all
 - name: zlib

# This can be single-test or pairwise-test
# pair-wise test implies we require 2 packages 
experiment:
  name: single-test
```


 
### Reproduce a Test

If you have a test case to share with a colleague or otherwise reproduce,
since all testing bases are uploaded to the quay.io registry, this is easy to do!
For example, let's say that we want to reproduce with testing base libabigail
and tests for mpich. We can use the [quay.io/buildsi/libabigail-test-mpich](https://quay.io/repository/buildsi/libabigail-test-mpich?tab=tags)
container. First (in case you have an old version) pull:

```bash
$ docker pull quay.io/buildsi/libabigail-test-zlib:latest
```

And then because the entrypoint is set to run the tests, we can just run the container!

```bash
$ docker run -it --rm quay.io/buildsi/libabigail-test-zlib:latest
====================================================== test session starts ======================================================
platform linux -- Python 3.8.5, pytest-6.2.4, py-1.10.0, pluggy-0.13.1
rootdir: /build-si
collected 21 items                                                                                                              

runtests.py Testing zlib@1.2.11 lib/libz.so with abidw
Testing lib/libz.so with abidw
...
```

And you would bind results to your host to save them locally.

```bash
mkdir -p results
$ docker run -it --rm -v $PWD/results:/results quay.io/buildsi/libabigail-test-zlib:latest
```

Or you can run tests interactively in the container:

```bash
$ docker run -it --rm --entrypoint bash quay.io/buildsi/libabigail-test-zlib:latest
root@6d2ea5dbddbf:/build-si# pytest -xs runtests.py 
```

Note that the entrypoint might vary based on the tester - libabigail uses a pytest script.
When you are done, the testing structure is the same as before - a nested tree
organized by tester, package, and versions so that all tests can live alongside
one another.

```
results/
└── libabigail
    └── 1.8.2
        ├── diff
        │   └── zlib
        │       └── zlib
        │           ├── 1.2.11-1.2.11
        │           ├── 1.2.11-1.2.11.log
        │           ├── 1.2.11-1.2.8
        │           ├── 1.2.11-1.2.8.log
        │           ├── 1.2.8-1.2.11
        │           ├── 1.2.8-1.2.11.log
        │           ├── 1.2.8-1.2.8
        │           └── 1.2.8-1.2.8.log
        └── zlib
            ├── 1.2.11
            │   └── lib
            │       ├── libz.so.xml
            │       └── libz.so.xml.log
            └── 1.2.8
                └── lib
                    ├── libz.so.xml
                    └── libz.so.xml.log

10 directories, 12 files
```

If you already have the container locally, you can also test with the script here:

```bash
./build-si-containers test zlib
```

or force a rebuild.

```bash
./build-si-containers test zlib --rebuild
```

It's up to you!

 
### Bolo's Notes

These are notes I derived from what Bolo sent me. I'm keeping them here for now
and will eventually refactor and remove them. First, pull the container:

```bash
$ docker pull bigtrak/si_mpich:1.1
```

This is a base that we can use to run tests for some version of libabigail and
other tools. For now, since I don't have the Dockerfile, we don't have control
of the versions inside the container (but we will).
If you want to derive a sense of the Dockerfile from the container, here is a means to do that:

```bash
$ alias dfimage="docker run -v /var/run/docker.sock:/var/run/docker.sock --rm alpine/dfimage"
$ dfimage -sV=1.36 bigtrak/si_mpich:1.1
```

The actual Dockerfile is currently not known, but will be added here when it is shared.
The base of the image is centos7 with its release compiler installed. We do
this intentionally because there are known issues with this version.

```bash
$ docker run -it bigtrak/si_mpich:1.1
```

This is centos7, with the release compiler installed.   This
is the distro gcc, which is intentional. We can re-run the existing analysis with the gen-* scripts. 
Best to rename the results dir, and then create a new one.  Then results can be compared, as well as timing information.

> We will refactor this so that libabigail is a runner that parses the mpich.yaml (or similar) config file, and then generates templates to run some set of commands, saving output to a structured/organized location.

This container has many layers in it.. this aids development quite a bit, but makes you download a lot of layers.  It's not all that
bad, it just seems that way.  The advantage for now is when I change or add something, you already have most of the layers and the delta
is tiny.    This is literally the first pass of the original with the newer libabgail added, nothing more!

> We will use autamus bases instead that can provide the already built software for a specific version, and then add another layer for some testing setup.

```bash
$ docker pull bigtrak/si_mpich:1.1

# (ps: do not download latest, which will not be this image,
# will be fixed later after I remedy my tagging problem.  Oops)
```
       
How to use this container?

```bash
docker run -it bigtrak/si_mpich:1.1
ls results
ls build
ls distrib
ls /opt
## results were built as part of the container.   TO rebuild them
##
mv results results-orig
mkdir results
./gen-dw
./gen-compat
./gen-diff
```

I would suggest getting in the container, pulling smeagle from its
git repository, building it and running it, analyzing the mpich
versions and seeing how it differs from libabigail.

> This is a great idea! We will eventually do this, when Smeagle is actually useful.

You can add whatever libraries you need with 'yum install'; you most likely want to install the "-devel" variant of the libraries to be able to compile against them. Same with editor of choice, etc.

```
Analysis Tools
--------------
libabigail-1.8          /opt
libabigail-1.8.2        /opt            upgrade

By default, the libabigail in the path is now 1.8.2.

MPICH Versions
--------------
mpich-1.5               /opt
mpich-3.2.1             /opt
mpich-3.3               /opt
mpich-3.3.2             /opt
mpich-3.4.1             /opt

These were compiled with the default vendor options, with
the addition of -g for dwarf symbols for libabigail.  3.4.1 is compiled
with the same transport as 3.3.2, as the versions are incompatible,
and are not an issue for our abi testing.

Trivial program to analyze
---------------------------
cpi -- compute pi from mpich test harness in mpich


Analysis results
-----------------
/build-si/results

The results of the comparison of the "base" 3.2.1 of mpich with
subsequent versions.

The .log files are the stderr, including timing information, and
human interpretation of libabigail status code.

Scripts to re-create results
-----------------------------
gen-dw
gen-compat
gen-diff
```

We will need to be able to output results in a way that can be compared across testing
libraries (e.g., Smeagle and libabigail).

## License

Spack is distributed under the terms of both the MIT license and the
Apache License (Version 2.0). Users may choose either license, at their
option.

All new contributions must be made under both the MIT and Apache-2.0
licenses.

See [LICENSE-MIT](https://github.com/spack/spack/blob/develop/LICENSE-MIT),
[LICENSE-APACHE](https://github.com/spack/spack/blob/develop/LICENSE-APACHE),
[COPYRIGHT](https://github.com/spack/spack/blob/develop/COPYRIGHT), and
[NOTICE](https://github.com/spack/spack/blob/develop/NOTICE) for details.

SPDX-License-Identifier: (Apache-2.0 OR MIT)

LLNL-CODE-811652
