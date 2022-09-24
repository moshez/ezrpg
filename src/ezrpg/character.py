from __future__ import annotations
import attrs
import random

@attrs.frozen
class Dice:
    num: int
    value: int
    _random: random.Random
    constant: int = attrs.field(default=0)
    
    def __int__(self):
        return sum(
            random.randrange(1, self.value + 1)
            for i in range(self.num)
        ) + self.constant

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
            maximum -= mod
        minimum = self.minimum
        if minimum is not None:
            minimum += mod
        
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
            

@attrs.frozen
class Character:
    notes: Mapping[str, str] = attrs.field(factory=dict)
    _moves: MoveCollection = attrs.field(factory=MoveCollection)
    traits: Mapping[str, int] = attrs.field(factory=dict)
    
    @property
    def moves(self):
        return self._moves.__get__(self)
    
@attrs.frozen
class Adjustment:
    trait: str
    factor: float
    constant: int
    
    def from_character(self, character):
        return int(character.traits[self.traint] * self.factor) + self.constant


@attrs.frozen
class Move:
    name: str
    threshold: Threshold
    description: str = attrs.field(default="")
    adjustments: Sequence[Adjustment] = attrs.field(factory=list)
    effect_adjustments: Sequence[Adjustment] = attrs.field(factory=list)
    
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
    
@attrs.frozen
class _CharacterMove:
    character: Character
    move: Move
    
    def __int__(self):
        return self.move.get_effect(self.character)
        
    