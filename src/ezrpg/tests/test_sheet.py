import unittest
import random
import textwrap

from hamcrest import (
    assert_that,
    string_contains_in_order,
    all_of,
    greater_than,
    less_than,
    not_,
    has_item,
    equal_to,
)

from .. import character, sheet


class TestCharacter(unittest.TestCase):
    def setUp(self):
        self.random = random.Random(6)
        dm = character.dice_maker(self.random)
        self.some_char = sheet.from_toml(dm, textwrap.dedent("""\
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
        """))

    def test_roll(self):
        punch = self.some_char.moves.punch
        results = [int(punch) for i in range(10)]
        zeroes = len([0 for x in results if x == 0])
        assert_that(zeroes, all_of(greater_than(5), less_than(15)))
        average = sum(results) / (len(results) - zeroes)
        assert_that(average, all_of(greater_than(10), less_than(20)))
