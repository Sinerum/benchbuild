import json
import typing as tp

from plumbum import TEE, local

from benchbuild.environments.domain import model
from benchbuild.settings import CFG
from benchbuild.utils.cmd import buildah, mktemp

BUILDAH_DEFAULT_OPTS = [
    '--root',
    str(CFG['container']['root']), '--runroot',
    str(CFG['container']['runroot'])
]

BUILDAH_DEFAULT_COMMAND_OPTS = ['--add-history']


def bb_buildah():
    return buildah[BUILDAH_DEFAULT_OPTS]


BB_BUILDAH_FROM = bb_buildah()['from']
BB_BUILDAH_BUD = bb_buildah()['bud']
BB_BUILDAH_ADD = bb_buildah()['add'][BUILDAH_DEFAULT_COMMAND_OPTS]
BB_BUILDAH_COMMIT = bb_buildah()['commit']
BB_BUILDAH_CONFIG = bb_buildah()['config']
BB_BUILDAH_COPY = bb_buildah()['copy'][BUILDAH_DEFAULT_COMMAND_OPTS]
BB_BUILDAH_IMAGES = bb_buildah()['images']
BB_BUILDAH_RUN = bb_buildah()['run'][BUILDAH_DEFAULT_COMMAND_OPTS]
BB_BUILDAH_RM = bb_buildah()['rm']
BB_BUILDAH_CLEAN = bb_buildah()['clean']
BB_BUILDAH_INSPECT = bb_buildah()['inspect']


def create_working_container(from_image: model.FromLayer) -> str:
    return BB_BUILDAH_FROM(from_image.base).strip()


def destroy_working_container(container: model.Container) -> None:
    BB_BUILDAH_RM[container.container_id] & TEE


def commit_working_container(container: model.Container) -> None:
    image = container.image
    BB_BUILDAH_COMMIT[container.container_id, image.name] & TEE


def spawn_add_layer(container: model.Container, layer: model.AddLayer) -> None:
    cmd = BB_BUILDAH_ADD[container.container_id][layer.sources][
        layer.destination]
    cmd & TEE


def spawn_run_layer(container: model.Container, layer: model.RunLayer) -> None:
    kws = []
    for name, value in dict(layer.kwargs).items():
        kws.append(f'--{name}')
        kws.append(f'{str(value)}')

    cmd = BB_BUILDAH_RUN[kws][container.container_id, '--',
                              layer.command][layer.args]
    cmd & TEE


def spawn_context_layer(container: model.Container,
                        layer: model.ContextLayer) -> None:
    tmpdir = mktemp('-dt', '-p', str(CFG['build_dir'])).strip()
    # Send ContextCreated event.

    with local.cwd(tmpdir):
        layer.func()


def spawn_clear_context_layer(container: model.Container,
                              layer: model.ClearContextLayer) -> None:
    pass


def find_image(tag: str) -> model.MaybeImage:
    results = BB_BUILDAH_IMAGES('--json', tag, retcode=[0, 125])
    if results:
        json_results = json.loads(results)
        if json_results:
            #json_image = json_results.pop(0)
            return model.Image(tag, model.FromLayer(tag), [])
    return None


LAYER_HANDLERS = {
    model.AddLayer: spawn_add_layer,
    model.ContextLayer: spawn_context_layer,
    model.CopyLayer: spawn_context_layer,
    model.RunLayer: spawn_run_layer,
    model.ClearContextLayer: spawn_clear_context_layer
}


def spawn_layer(container: model.Container, layer: model.Layer) -> None:
    handler = LAYER_HANDLERS[type(layer)]
    handler(container, layer)
