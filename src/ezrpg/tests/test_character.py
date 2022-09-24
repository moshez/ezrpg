import unittest
import random
from hamcrest import (
    assert_that,
    string_contains_in_order,
    all_of,
    greater_than,
    less_than,
    not_,
    has_item,
)

from .. import character


class TestCharacter(unittest.TestCase):
    def setUp(self):
        self.random = random.Random(6)
        dm = character.dice_maker(self.random)
        self.some_char = character.Character(
            name="Awesome Man",
            traits=dict(
                STR=10,
                DEX=20,
            ),
            moves=character.moves(
                character.Move(
                    "punch",
                    description="Throw a punch",
                    threshold=character.Threshold(
                        threshold_dice=dm("3d6"),
                        effect=dm("4d6"),
                        maximum=10,
                    ),
                ),
                character.Move(
                    "throw",
                    description="Throw an item",
                    threshold=character.Threshold(
                        threshold_dice=dm("3d6"),
                        effect=dm("2d6"),
                        maximum=10,
                    ),
                    adjustments=[
                        character.Adjustment(trait="DEX", factor=3, constant=-3)
                    ],
                ),
            ),
        )

    def test_display(self):
        assert_that(
            self.some_char._repr_html_(),
            string_contains_in_order("Awesome", "STR", "10", "punch"),
        )

    def test_roll(self):
        punch = self.some_char.moves.punch
        results = [int(punch) for i in range(10)]
        zeroes = len([0 for x in results if x == 0])
        assert_that(zeroes, all_of(greater_than(5), less_than(15)))
        average = sum(results) / (len(results) - zeroes)
        assert_that(average, all_of(greater_than(10), less_than(20)))

    def test_roll_with_adjustment(self):
        throw = self.some_char.moves.throw
        results = [int(throw) for i in range(10)]
        assert_that(results, not_(has_item(0)))
