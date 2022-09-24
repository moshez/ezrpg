from __future__ import annotations
import attrs
import random

@attrs.frozen
class _Dice:
    num: int
    value: int
    _random: random.Random
    constant: int = attrs.field(default=0)
    
    def __int__(self):
        return sum(
            self._random.randrange(1, self.value + 1)
            for i in range(self.num)
        ) + self.constant

def dice_maker(rnd: random.Random):
    def make_die(desc: str):
        num, value = map(int, desc.split("d"))
        return _Dice(num=num, value=value, random=rnd)
    return make_die

@attrs.frozen
class Threshold:
    threshold_dice: Dice
    effect: Union[int, bool, Dice]
    no_effect: Union[int, bool, Dice] = attrs.field(default=0)
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
            

def _empty_move_collection():
    return MoveCollection(moves={})

@attrs.frozen
class Character:
    name: str
    notes: Mapping[str, str] = attrs.field(factory=dict)
    _moves: MoveCollection = attrs.field(factory=_empty_move_collection)
    traits: Mapping[str, int] = attrs.field(factory=dict)
    
    @property
    def moves(self):
        return self._moves.__get__(self)
    
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
    
    def from_character(self, character):
        return int(character.traits[self.trait] * self.factor) + self.constant


@attrs.frozen
class Move:
    name: str
    threshold: Threshold
    description: str = attrs.field(default="")
    adjustments: Sequence[Adjustment] = attrs.field(factory=list)
    effect_adjustments: Sequence[Adjustment] = attrs.field(factory=list)
    
    def adjust(self, adjustment):
        return attrs.evolve(self, adjustments=self.adjustments + [threshold.adjust])

    def get_effect(self, character):
        threshold = self.threshold
        for adjustment in self.adjustments:
            threshold = threshold.adjust(
                adjustment.from_character(character),
            )
        for effect_adjustment in self.effect_adjustments:
            threshold.effect.constant += \
                effect_adjustment.from_character(character)
        return int(threshold)
    
    def __get__(self, instance, owner=None):
        return _CharacterMove(character=instance, move=self)
    
@attrs.frozen
class MoveCollection:
    moves: Mapping[str, Move]
    
    def __get__(self, instance, owner=None):
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
        except KeyError:
            raise AttributeError(name)
        else:
            return the_move.__get__(self.character)
    
    def __iter__(self):
        return iter(self.collection.moves.values())
    
@attrs.frozen
class _CharacterMove:
    character: Character
    move: Move
    
    def __int__(self):
        return self.move.get_effect(self.character)
        
    