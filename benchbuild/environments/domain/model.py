import abc
import typing as tp

import attr

from benchbuild.environments.domain import events


@attr.s
class Layer(abc.ABC):
    pass


@attr.s(frozen=True)
class FromLayer(Layer):
    base: str = attr.ib()


@attr.s(frozen=True)
class AddLayer(Layer):
    sources: tp.List[str] = attr.ib()
    destination: str = attr.ib()


@attr.s(frozen=True)
class CopyLayer(Layer):
    sources: tp.List[str] = attr.ib()
    destination: str = attr.ib()


@attr.s(frozen=True)
class RunLayer(Layer):
    command: str = attr.ib()
    args: tp.List[str] = attr.ib()


@attr.s(frozen=True)
class ContextLayer(Layer):
    func: tp.Callable[[], None] = attr.ib()


@attr.s(frozen=True)
class ClearContextLayer(Layer):
    func: tp.Callable[[], None] = attr.ib()


@attr.s
class Image:
    name: str = attr.ib()
    from_: FromLayer = attr.ib()
    layers: tp.List[Layer] = attr.ib(factory=list)

    def append(self, layer: Layer) -> None:
        self.layers.append(layer)

    def prepend(self, layer: Layer) -> None:
        self.layers = [layer].extend(self.layers)


MaybeImage = tp.Optional[Image]


@attr.s
class Container:
    container_id: str = attr.ib()
    image: Image = attr.ib()

    events = attr.ib(factory=list)  # type: tp.List[events.Event]
