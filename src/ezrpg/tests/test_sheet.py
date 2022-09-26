import unittest
import random
import textwrap

from hamcrest import (
    assert_that,
    all_of,
    greater_than,
    less_than,
    equal_to,
)

from .. import character, sheet


class TestCharacter(unittest.TestCase):
    def setUp(self):
        self.random = random.Random(6)
        self.dm = character.dice_maker(self.random)

    def test_roll(self):
        some_char = sheet.from_toml(
            self.dm,
            textwrap.dedent(
                """\
        [general]
        name="Awesome Man"
        STR=10
        DEX=20

        [moves.default]
        roll="3d6"
        effect=true

        [moves.punch]
        effect = "4d6"
        succeed = "<10"

        [[moves.punch.effect_adjustments]]
        trait = "STR"
        factor = 0.2

        [moves.save]
        succeed = ">9"

        [[moves.save.adjustments]]
        constant = 1

        [moves.climbing]
        succeed = "<9"
        effect = "1"
        """
            ),
        )

        punch = some_char.moves.punch
        results = [int(punch) for i in range(10)]
        zeroes = len([0 for x in results if x == 0])
        assert_that(zeroes, all_of(greater_than(5), less_than(15)))
        average = sum(results) / (len(results) - zeroes)
        assert_that(average, all_of(greater_than(10), less_than(20)))

    def test_bonus_effect(self):
        some_char = sheet.from_toml(
            self.dm,
            textwrap.dedent(
                """\
                [general]
                name = "Example Character"
                Arcane_Lore = 2

                [moves]
                lore = {}
                lore_arcane = {}

                [moves.default]
                roll="4d3"
                succeed=">4"
                effect=1

                [[moves.default.bonus_effect]]
                level = 1
                value = 2

                [[moves.default.bonus_effect]]
                level = 3
                value = 3

                [[moves.lore_arcane.adjustments]]
                trait = "Arcane_Lore"
                """
            ),
        )
        assert_that(int(some_char.moves.lore_arcane), equal_to(3))
