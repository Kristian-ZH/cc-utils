# SPDX-FileCopyrightText: 2020 SAP SE or an SAP affiliate company and Gardener contributors
#
# SPDX-License-Identifier: Apache-2.0

FROM eu.gcr.io/gardener-project/cc/job-image-base:0.44.0

COPY . /cc/utils/

# place version file into container's filesystem to make it easier to
# determine the image version during runtime
COPY ci/version /metadata/VERSION

# XXX backards compatibility (remove eventually)
ENV PATH /cc/utils/:/cc/utils/bin:$PATH

RUN pip3 install --upgrade \
  --find-links /cc/utils/dist \
  gardener-cicd-libs \
  gardener-cicd-cli \
  gardener-cicd-whd \
  gardenlinux \
&& pip3 uninstall -y gardener-component-model \
&& pip3 install gardener-component-model

RUN EFFECTIVE_VERSION="$(cat /metadata/VERSION)" REPO_DIR=/cc/utils \
  /cc/utils/.ci/bump_job_image_version.py
