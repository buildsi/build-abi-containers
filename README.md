# Build ABI Containers

**under development**

The goal of this repository is to provide container environments for
evaluating ABI, and to run tests for ABI in the CI. The approach we take is the following:

 - provide base containers with tools to test abi.
 - For some number of packages, define libraries and binaries within to build and test.
 - Build a testing container on top of a base container, with an [autamus](https://autamus.io) package added via multi-stage build. We might change this to use a spack build cache instead, but right now I'm testing with autamus containers.
 - Run the entrypoint of the container with a local volume to run tests and generate output.

## Organization

 - [docker](docker): includes `Dockerfile`s, one per testing base, that will be deployed to [quay.io/buildsi](https://quay.io/organization/buildsi).
 - [tests](tests): includes yaml config files that are matched to a spack package to test (or more generally an autamus container). The configs are validated when loaded.
 - [testers](testers): is a folder of tester subdirectories, which should be named for the tester (e.g., libabigail). No other files should be put in this folder root.
 - [templates](templates): includes both container build templates, and tester runtime templates. The container build templates.

## Usage

The client exposes two commands - to build and run tests:

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
testers folder), a tester name (we only have one now, so it defaults to libabigail),
and if we should use the spack build cache to install (not recommended currently as
it doesn't have most of what we need)

```bash
usage: build-si-containers build [-h] [--root ROOT] [--use-cache] [--tester {libabigail,all}] packages [packages ...]

positional arguments:
  packages              packages to test

optional arguments:
  -h, --help            show this help message and exit
  --root ROOT, -r ROOT  The root with the tests and testers directories.
  --use-cache           Install from build cache instead of autamus.
  --tester {libabigail,all}, -t {libabigail,all}
                        The tester to run tests for.
```

We will be doing a multi-stage build with a testing base from [quay.io/buildsi](https://quay.io/organization/buildsi), combined with a package of interest from [autamus](https://autamus.io). The container from autamus currently has multiple versions
of the same package installed, as this is what Bolo was doing. But we can change this to, for
example, install any set of packages on demand from a spack build cache. So to build the container
for example to test "mpich" which has a yaml file in
[tests](tests), you can do:

```bash
./build-si-containers build mpich
```

If we can add these steps to CI, perhaps on any change of a tester or package, then
the containers will be ready to go to produce results. By default, we use
container bases from autamus. But if you want to give the build cache a shot
(maybe if we can update it to include more packages?) you can do:

```bash
./build-si-containers build --use-cache mpich
```

#### 2. Run Tests

Once your container is built, testing is just running it!

```bash
$ docker run -it quay.io/buildsi/libabigail-test-mpich:latest
```

You can also request build and tests to be run at the same time:

```bash
./build-si-containers test mpich
```

While the build command will always do a build, the test command will first
look to see if the container already has been built, and not rebuild it if
this is the case. To force a rebuild:


```
./build-si-containers test --rebuild mpich
```

By default, results are saved to the present working directory in a "results"
folder. The structure of the folder is done, so that results from different
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

### Add a Tester

A tester is a base for running some kind of test on a binary. When you add a tester,
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
defines metadata like the tester's name (matching the folder), an 
entrypoint, and runscript for the container (written to `/build-si/`) along
with the active version. Since we typically want to consistently test using one
version, for now it is designed in this way. So you should write
a config file named `tester.yaml` in the [testers](testers) directory in a subfolder
named for the tester. For example, libabigail looks like this:

```yaml
tester:
  name: libabigail
  version: 1.8.2
  runscript: runtests.sh
  entrypoint: /bin/bash
```

Notice the bin folder? Any files that you add in bin will be added to /usr/local/bin, the idea being
you can write extra scripts for the tester to use. For now, we are just supporting one version of a tester.

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
of these containers is to provide a base with the testing software, onto which
we can install a package and run tests. This means that to add a new testing base, you should:

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

In each of [deploy-containers.yaml](.github/workflows/deploy-containers.yaml) and [build-containers.yaml](.github/workflows/build-containers.yaml) we discover a list of testers by way of listing subfolders in the [testers](testers) directory.
Then, for each changed file (according to git history), we trigger a new build. Versions
for one or more of these builds are derived from the `versions` text file we created earlier.
And that's it! When a file is changed in one of these folders, it will be built with CI via `build-containers.yaml`
and then deployed on merge to master with `deploy-containers.yaml`

**Note: You should always merge only one clean commit into master, so take care to rebase in PRs and write good messages!**

These are the bases we add packages on top of, and then run tests.

### Add a Test

Adding a test comes down to:

1. Adding a yaml file in the [tests](tests) folder named according to the package (or group) to test.
2. If build caches are not available, ensuring an autamus container is built in [buildsi](https://github.com/autamus/registry/tree/main/containers/buildsi/) namespace.

In the [tests](tests) folder, you will find different families of packages to test.
For example, the `mpich.yaml` file will eventually build different containers to
test each tester (e.g., libabigail) against for some number of versions and
libraries. Here is what that looks like:

```yaml
package:
 name: mpich
 versions:
  - "3.2.1"
  - "3.3"
  - "3.3.2"
  - "3.4.1"
  - "2-1.5"
 headers:
  - include
 libs:
  - libs/libmpich.so
```

Currently, we are developing with matching autamus containers (e.g., asking
to test mpich will use [this container](https://github.com/orgs/autamus/packages/container/package/buildsi-mpich)) 
but once we have a build cache to quickly install from, it should be possible to write any number of packages in
a file. For now, each of these packages (and the versions requested) will need to be available
on the autamus registry, which means that:

 - we need to be able to build with debug symbols globally
 - strip needs to be set to false
 - autamus needs to be able to build older versions of libraries on request.
 
We could install with spack natively, but we will save a lot of time using
pre-built layers. Note that the scripts to make this happen aren't developed
yet - we just have the base containers.

 
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

This container has many layers in it. This aids development quite a bit, but makes you download a lot of layers.  It's not all that
bad, it just seems that way.  The advantage, for now, is when I change or add something, you already have most of the layers, and the delta
is tiny.    This is literally the first pass of the original with the newer libabgail added, nothing more!

> We will use autamus bases instead to provide the already built software for a specific version, and then add another layer for some testing setup.

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

> This is a great idea! We will eventually do this when Smeagle is actually useful.

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
