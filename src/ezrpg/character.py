from __future__ import annotations
from typing import Mapping, Union, Optional, Sequence, Protocol

import attrs
import random
import logging

LOGGER = logging.getLogger(__name__)


class Intable(Protocol):
    """
    Something convertable to an int.

    The EZ-RPG system converts to int representing
    "effect size".
    """

    def __int__(self) -> int:
        "The value/effect"


class IntableFromCharacter(Protocol):
    """
    Something creating an int from a character
    """

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
    """
    Create dice representing things like 4d6+2

    Args:
        rnd: The source of randomness

    Returns:
        A function converting die description to intable things.
    """

    def make_die(desc: Union[str, int]) -> Union[int, _Dice]:
        if isinstance(desc, int):
            return desc
        if "d" not in desc:
            return int(desc)
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
        )

    return make_die


@attrs.frozen
class Threshold:
    """
    Different effects based on thresholds
    """

    threshold_dice: _Dice
    effect: Union[int, bool, _Dice]
    no_effect: Union[int, bool, _Dice] = attrs.field(default=0)
    bonus_effect: Mapping[int, Union[int, bool, _Dice]] = attrs.field(factory=dict)
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
        def get_effect():
            success_roll = int(self.threshold_dice)
            succeeded_by = 10
            if self.maximum is not None:
                succeeded_by = min(self.maximum - success_roll, succeeded_by)
            if self.minimum is not None:
                succeeded_by = min(success_roll - self.minimum, succeeded_by)
            LOGGER.info("Succeeded by %s", succeeded_by)
            if succeeded_by < 0:
                return self.no_effect
            special_success = [
                level for level in self.bonus_effect if level <= succeeded_by
            ]
            if len(special_success) > 0:
                return self.bonus_effect[max(special_success)]
            return self.effect

        return int(get_effect())


def _empty_move_collection() -> MoveCollection:  # pragma: no cover
    return MoveCollection(moves={})


@attrs.frozen
class Character:
    """
    An RPG character
    """

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
    factor: float = attrs.field(default=1)
    constant: int = attrs.field(default=0)

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
                effect = _Dice(0, 6, random.Random(), effect)
            constant = effect.constant
            for effect_adjustment in self.effect_adjustments:
                constant += effect_adjustment.from_character(character)
            threshold = attrs.evolve(
                threshold, effect=attrs.evolve(effect, constant=constant)
            )
        LOGGER.info("Adjusted threshold: %s", threshold)
        return int(threshold)

    def adjust(self, adjustment: IntableFromCharacter) -> Move:
        all_adjustments = list(self.adjustments)
        all_adjustments.append(adjustment)
        return attrs.evolve(self, adjustments=all_adjustments)

    def from_character(self, instance: Character) -> Intable:
        return _CharacterMove(character=instance, move=self)


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
