# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *


class Tim(MakefilePackage):
    homepage = "https://github.com/buildsi/build-abi-test-tim"
    git = "https://github.com/buildsi/build-abi-test-tim.git"

    version('main', branch='main')
    # Does not have releases yet!

    depends_on("elfutils")
    
    def install(self, spec, prefix):
        mkdir(prefix.bin)
        mkdir(prefix.lib)
        install('test', prefix.bin)
        install('reader', prefix.bin)
        install('libfoo.so', prefix.lib)
