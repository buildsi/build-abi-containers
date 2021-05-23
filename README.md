# Build ABI Containers

**under development**

The goal of this repository is to provide container environments for
evaluating ABI, and to run tests for ABI in the CI. We currently just have one container that provides several
examples, and eventually will likely have multiple. The approach we take is the following:

 - provide base containers with tools to test abi. This means that we have base containers with spack, and then derivations of those with different ABI testing libraries.
 - For some number of packages, define libraries and binaries within to build and test.
 - generate output logs for different tools

## Organization

 - [docker](docker): includes `Dockerfile`s, one per testing base, that will be deployed to [quay.io/buildsi](https://quay.io/organization/buildsi).
 - [templates](templates): includes container build templates that can start with an autamus base container for some package, and then add layers for the testing software (e.g., libabigail and eventually smeagle). I might also test just installing directly from spack, not decided yet.

## Development Notes

### How will it work?

In the [tests](tests) folder you will find different families of packages to test.
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

Each of these packages (and the versions requested) will need to be available
on the autamus registry, which means that:

 - we need to be able to build with debug symbols globally
 - strip needs to be set to false
 - autamus needs to be able to build older versions of libraries on request.
 
We could install with spack natively, but we will save a lot of time using
pre-built layers. Note that the scripts to make this happen aren't developed
yet - I need to create the base containers first.

 
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
