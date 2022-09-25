from __future__ import annotations

import functools
import toml

from . import character

def _from_move_data(dice_maker: Callable, move: Mapping[str, Any]) -> character.Move:
    if move["succeed"].startswith("<"):
        maximum, minimum = int(move["succeed"][1:]), None
    elif move["succeed"].startswith(">"):
        maximum, minimum = None, int(move["succeed"][1:])
    else: # pragma: no cover
        raise ValueError("unknown threshold", move)
    effect = move.pop("effect")
    if isinstance(effect, int):
        effect = effect
    else:
        effect = dice_maker(effect)
    return character.Move(
        name=move["name"],
        threshold=character.Threshold(
            threshold_dice=dice_maker(move["roll"]),
            maximum=maximum,
            minimum=minimum,
            effect=effect,
            ),
        adjustments=[_from_adjustment_data(adjustment) 
                     for adjustment in move.get("adjustments", [])],
        effect_adjustments=[_from_adjustment_data(adjustment) 
                     for adjustment in move.get("effect_adjustments", [])],
    )

def _from_adjustment_data(adjustment: Mapping[str, Any]) -> character.IntableFromCharacter:
    if "trait" in adjustment:
        return character.Adjustment(**adjustment)
    else:
        return character.ConstantAdjustment(**adjustment)

def from_toml(dice_maker: Callable, toml_data: str) -> character.Character:
    data = toml.loads(toml_data)
    moves = data.setdefault("moves", {})
    default = moves.pop("default", {})
    for name, a_move in moves.items():
        missing = set(default.keys()) - set(a_move.keys())
        a_move.update({key: default[key] for key in missing})
        a_move["name"] = name
    return character.Character(
        name=data["general"].pop("name"),
        traits=data["general"],
        moves=character.moves(
            *map(functools.partial(_from_move_data, dice_maker), moves.values())
        ),
    )
