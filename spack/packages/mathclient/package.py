# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *


class Mathclient(MakefilePackage):
    homepage = "https://github.com/buildsi/build-abi-test-mathclient"
    url = "https://github.com/buildsi/build-abi-test-mathclient/archive/refs/tags/2.0.0.tar.gz"

    version('1.0.0', sha256='84646caa33f635f8701a9d261b1bfb5ac52b6c62ab07766504ca580bc265f5ec')
    version('2.0.0', sha256='215e66e131f769de06cee43009fdc8ab85494d9e1559b07ddb79866f78665e0d')

    def install(self, spec, prefix):
        mkdir(prefix.bin)
        mkdir(prefix.lib)
        install('math-client', prefix.bin)
        install('libmath.so', prefix.lib)
