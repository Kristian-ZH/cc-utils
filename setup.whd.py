# SPDX-FileCopyrightText: 2019 SAP SE or an SAP affiliate company and Gardener contributors
#
# SPDX-License-Identifier: Apache-2.0

import setuptools
import os

own_dir = os.path.abspath(os.path.dirname(__file__))


def requirements():
    yield 'gardener-cicd-libs'
    yield 'gardener-cicd-cli'

    with open(os.path.join(own_dir, 'requirements.whd.txt')) as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            yield line


def modules():
    return [
    ]


def version():
    with open(os.path.join(own_dir, 'ci', 'version')) as f:
        return f.read().strip()


setuptools.setup(
    name='gardener-cicd-whd',
    version=version(),
    description='Gardener CI/CD Webhook Dispatcher',
    python_requires='>=3.8.*',
    py_modules=modules(),
    packages=['whd'],
    package_data={
        'ci':['version'],
    },
    install_requires=list(requirements()),
    entry_points={
    },
)
