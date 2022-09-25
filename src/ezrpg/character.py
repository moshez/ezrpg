from __future__ import annotations
from typing import Mapping, Union, Optional, Sequence, Protocol

import attrs
import random
import logging

LOGGER = logging.getLogger(__name__)


class Intable(Protocol):
    def __int__(self) -> int:
        "The value/effect"


class IntableFromCharacter(Protocol):
    def from_character(self, character: Character) -> int:
        "The value/effect"


@attrs.frozen
class _Dice:
    num: int
    value: int
    _random: random.Random
    constant: int = attrs.field(default=0)

    def __int__(self):
        ret_value = sum(
            self._random.randrange(1, self.value + 1) for i in range(self.num)
        )
        ret_value += self.constant
        LOGGER.info("Rolled %s, got %s", self, ret_value)
        return ret_value


def dice_maker(rnd: random.Random):
    def make_die(desc: str):
        try:
            die, constant = desc.split("+")
        except ValueError:
            die, constant = desc, "0"
        the_constant = int(constant)
        num, value = map(int, die.split("d"))
        return _Dice(
            num=num,
            value=value,
            constant=the_constant,
            random=rnd,
        )  # type: ignore

    return make_die


@attrs.frozen
class Threshold:
    threshold_dice: _Dice
    effect: Union[int, bool, _Dice]
    no_effect: Union[int, bool, _Dice] = attrs.field(default=0)
    maximum: Optional[int] = attrs.field(default=None)
    minimum: Optional[int] = attrs.field(default=None)

    def adjust(self, mod: int) -> Threshold:
        maximum = self.maximum
        if maximum is not None:
            maximum += mod
        minimum = self.minimum
        if minimum is not None:
            minimum -= mod

        return attrs.evolve(self, maximum=maximum, minimum=minimum)

    def __int__(self):
        def success():
            success_roll = int(self.threshold_dice)
            if self.maximum is not None and success_roll > self.maximum:
                return False
            if self.minimum is not None and success_roll < self.minimum:
                return False
            return True

        if success():
            return int(self.effect)
        else:
            return int(self.no_effect)


def _empty_move_collection() -> MoveCollection:  # pragma: no cover
    return MoveCollection(moves={})  # type: ignore


@attrs.frozen
class Character:
    name: str
    notes: Mapping[str, str] = attrs.field(factory=dict)
    _moves: MoveCollection = attrs.field(factory=_empty_move_collection)
    traits: Mapping[str, int] = attrs.field(factory=dict)

    @property
    def moves(self) -> _BoundMoveCollection:
        return self._moves.from_character(self)

    def _repr_html_(self):
        def html_bits():
            yield "<table>"
            yield "<tr>"
            yield "<td>"
            yield self.name
            yield "<td>"
            yield "<tr>"
            for name, value in self.traits.items():
                yield "<tr>"
                yield "<td>"
                yield name
                yield "</td>"
                yield "<td>"
                yield str(value)
                yield "</td>"
                yield "<tr>"
            for move in self.moves:
                yield "<tr>"
                yield "<td>"
                yield move.name
                yield "</td>"
                yield "<td>"
                yield move.description
                yield "</td>"
                yield "<tr>"
            yield "</tr>"
            yield "<table>"

        return "".join(html_bits())


@attrs.frozen
class Adjustment:
    trait: str
    factor: float
    constant: int

    def from_character(self, character: Character) -> int:
        return int(character.traits[self.trait] * self.factor) + self.constant


@attrs.frozen
class ConstantAdjustment:
    constant: int

    def from_character(self, character: Character) -> int:
        return self.constant


@attrs.frozen
class Move:
    name: str
    threshold: Threshold
    description: str = attrs.field(default="")
    adjustments: Sequence[IntableFromCharacter] = attrs.field(factory=list)
    effect_adjustments: Sequence[IntableFromCharacter] = attrs.field(factory=list)

    def get_effect(self, character: Character) -> int:
        threshold = self.threshold
        for adjustment in self.adjustments:
            threshold = threshold.adjust(
                adjustment.from_character(character),
            )
        if len(self.effect_adjustments) > 0:
            effect = threshold.effect
            if isinstance(effect, int):
                effect = _Dice(0, 6, random.Random(), effect)  # type: ignore
            constant = effect.constant
            for effect_adjustment in self.effect_adjustments:
                constant += effect_adjustment.from_character(character)
            threshold = attrs.evolve(
                threshold, effect=attrs.evolve(effect, constant=constant)
            )
        return int(threshold)

    def adjust(self, adjustment: IntableFromCharacter) -> Move:
        all_adjustments = list(self.adjustments)
        all_adjustments.append(adjustment)
        return attrs.evolve(self, adjustments=all_adjustments)

    def from_character(self, instance: Character) -> Intable:
        return _CharacterMove(character=instance, move=self)  # type: ignore


@attrs.frozen
class MoveCollection:
    moves: Mapping[str, Move]

    def from_character(self, instance):
        return _BoundMoveCollection(character=instance, collection=self)


def moves(*args):
    return MoveCollection(
        moves={a_move.name: a_move for a_move in args},
    )


@attrs.frozen
class _BoundMoveCollection:
    character: Character
    collection: MoveCollection

    def __getattr__(self, name):
        try:
            the_move = self.collection.moves[name]
        except KeyError:  # pragma: no cover
            raise AttributeError(name)
        else:
            return the_move.from_character(self.character)

    def __iter__(self):
        return iter(self.collection.moves.values())


@attrs.frozen
class _CharacterMove:
    character: Character
    move: Move

    def adjust(self, adjustment: IntableFromCharacter):
        return attrs.evolve(self, move=self.move.adjust(adjustment))

    def __int__(self):
        return self.move.get_effect(self.character)
