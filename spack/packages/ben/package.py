# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *


class Ben(MakefilePackage):
    homepage = "https://github.com/buildsi/build-abi-test-ben"
    url = "https://github.com/buildsi/build-abi-test-ben/archive/refs/tags/2.0.0.tar.gz"
    git = "https://github.com/buildsi/build-abi-test-ben.git"

    version('main', branch='main')
    version('1.0.0', sha256='28d85b076c7127934b1127c1695bbdc16e59ec5a42def68478c938835fbe114f')
    version('2.0.0', sha256='d913cf8de6ed92c836388bc7a492e0f975e589bab7616d99607180559d487d72')

    def install(self, spec, prefix):
        mkdir(prefix.bin)
        mkdir(prefix.lib)
        install('underlinktest', prefix.bin)
        install('librttiexcep.so', prefix.lib)
        install('libunderlink.so', prefix.lib)
