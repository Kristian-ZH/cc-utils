# SPDX-FileCopyrightText: 2019 SAP SE or an SAP affiliate company and Gardener contributors
#
# SPDX-License-Identifier: Apache-2.0

import os

import kube.ctx
import landscape_setup.concourse as setup_concourse

from ci.util import (
    ctx,
    CliHints,
    CliHint,
)
from concourse import client
from concourse.util import (
    sync_org_webhooks,
    resurrect_pods,
)
from concourse.enumerator import (
    DefinitionDescriptorPreprocessor,
    GithubOrganisationDefinitionEnumerator,
    SimpleFileDefinitionEnumerator,
    TemplateRetriever,
)
from concourse.replicator import (
    FilesystemDeployer,
    PipelineReplicator,
    Renderer,
)


def render_pipeline(
    definition_file: CliHints.existing_file(),
    template_path: CliHints.existing_dir(),
    cfg_name: str,
    out_dir: CliHints.existing_dir(),
    template_include_dir: str=None,
):
    cfg_factory = ctx().cfg_factory()
    cfg_set = cfg_factory.cfg_set(cfg_name=cfg_name)

    def_enumerators = [
        SimpleFileDefinitionEnumerator(
            definition_file=definition_file,
            cfg_set=cfg_set,
            repo_path='example/example',
            repo_branch='master',
            repo_host='github.com',
        )
    ]

    preprocessor = DefinitionDescriptorPreprocessor()

    if not template_include_dir:
        template_include_dir = template_path

    template_retriever = TemplateRetriever(template_path=template_path)
    renderer = Renderer(
        template_retriever=template_retriever,
        template_include_dir=template_include_dir,
        cfg_set=cfg_set,
    )

    deployer = FilesystemDeployer(base_dir=out_dir)

    replicator = PipelineReplicator(
        definition_enumerators=def_enumerators,
        descriptor_preprocessor=preprocessor,
        definition_renderer=renderer,
        definition_deployer=deployer
    )

    replicator.replicate()


def render_pipelines(
        template_path: str,
        config_name: str,
        out_dir: str,
        template_include_dir: str = None,
):
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    cfg_factory = ctx().cfg_factory()
    config_set = cfg_factory.cfg_set(cfg_name=config_name)

    concourse_cfg = config_set.concourse()
    job_mapping_set = cfg_factory.job_mapping(concourse_cfg.job_mapping_cfg_name())

    if not template_include_dir:
        template_include_dir = template_path

    def_enumerators = []
    for job_mapping in job_mapping_set.job_mappings().values():
        def_enumerators.append(
            GithubOrganisationDefinitionEnumerator(
                job_mapping=job_mapping,
                cfg_set=config_set
            )
        )

    preprocessor = DefinitionDescriptorPreprocessor()

    template_retriever = TemplateRetriever(template_path=[template_path])
    renderer = Renderer(
        template_retriever=template_retriever,
        template_include_dir=template_include_dir,
        cfg_set=config_set,
    )

    deployer = FilesystemDeployer(base_dir=out_dir)

    replicator = PipelineReplicator(
        definition_enumerators=def_enumerators,
        descriptor_preprocessor=preprocessor,
        definition_renderer=renderer,
        definition_deployer=deployer,
    )

    replicator.replicate()


def sync_org_webhooks_from_cfg(
    whd_deployment_config_name: str,
):
    '''
    Set or update all org-webhooks for the given configs.
    '''
    cfg_factory = ctx().cfg_factory()
    whd_deployment_cfg = cfg_factory.webhook_dispatcher_deployment(whd_deployment_config_name)
    sync_org_webhooks(whd_deployment_cfg)


def trigger_resource_check(
    cfg_name: CliHints.non_empty_string(help="cfg_set to use"),
    team_name: CliHints.non_empty_string(help="pipeline's team name"),
    pipeline_name: CliHints.non_empty_string(help="pipeline name"),
    resource_name: CliHints.non_empty_string(help="resource to check"),
):
    '''Triggers a check of the specified Concourse resource
    '''
    cfg_factory = ctx().cfg_factory()
    cfg_set = cfg_factory.cfg_set(cfg_name)
    concourse_cfg = cfg_set.concourse()
    api = client.from_cfg(
        concourse_cfg=concourse_cfg,
        team_name=team_name,
    )
    api.trigger_resource_check(
        pipeline_name=pipeline_name,
        resource_name=resource_name,
    )


def set_teams(
    config_name: CliHint(typehint=str, help='the cfg_set name to use'),
):
    config_factory = ctx().cfg_factory()
    config_set = config_factory.cfg_set(cfg_name=config_name)
    config = config_set.concourse()

    setup_concourse.set_teams(config=config)


def start_worker_resurrector(
    config_name: CliHint(typehint=str, help='the config set name to use'),
    concourse_namespace='concourse',
):
    config_factory = ctx().cfg_factory()
    config_set = config_factory.cfg_set(cfg_name=config_name)
    kubernetes_cfg = config_set.kubernetes()
    kube_client = kube.ctx.Ctx()
    kube_client.set_kubecfg(kubernetes_cfg.kubeconfig())

    concourse_cfg = config_set.concourse()
    concourse_client = client.from_cfg(concourse_cfg=concourse_cfg, team_name='main')

    resurrect_pods(
        namespace=concourse_namespace,
        concourse_client=concourse_client,
        kubernetes_client=kube_client
    )
