import unittest

from match import Match, Ability, Chance, Player, Phases, active_map, passive_map
from network import Network, Flags


class TestServerMethods(unittest.TestCase):

    """
        --------
        SPRINT 3
        --------
    """

    # Set up player with two cats
    def setUp(self):

        cats = [0, 1]
        self.player = Player("Moosey", None, cats)

    def test_int_3byte(self):

        ba = Network.int_3byte(Flags.ERROR)
        ba.append(Flags.ERROR)
        self.assertEqual(str(ba), "bytearray(b'\\x00\\x00\\x03\\x03')")

    # Test player cat property
    def test_player_cat(self):

        self.player.cat = 0
        self.assertEqual(self.player.cat, 0)
        self.assertEqual(self.player.health, 8)
        self.assertIsNotNone(self.player.cat)
        self.assertNotEqual(self.player.health, 0)
        self.assertTrue(self.player.cat is not None)

    # Test player chance_card property
    def test_player_chance(self):

        chance_card = self.player.chance_card
        self.assertIsNone(chance_card)

        self.player.chance_cards.append(0)
        chance_card = self.player.chance_card
        self.assertEqual(chance_card, 0)

        self.player.chance_cards.append(1)
        chance_card = self.player.chance_card
        self.assertEqual(chance_card, 1)

    # Test match select_cat function
    def test_select_cat(self):

        # Check non existent cat
        valid_cat = Match.select_cat(self.player, 3)
        self.assertFalse(valid_cat)

        # Check existent cat and health for assigned cat
        valid_cat = Match.select_cat(self.player, 1)
        self.assertTrue(valid_cat)
        self.assertEqual(self.player.health, 10)

        # Add a cat and check if still working

        self.player.cats.append(2)
        valid_cat = Match.select_cat(self.player, 2)
        self.assertTrue(valid_cat)
        self.assertEqual(self.player.cat, 2)
        self.assertEqual(self.player.health, 12)

    # Test Chance random_chances function
    def test_random_chances(self):

        self.assertEqual(len(self.player.chance_cards), 0)
        Chance.random_chances(self.player)
        self.assertEqual(len(self.player.chance_cards), 2)

    # Test Chance has_chance function
    def test_has_chance(self):

        has_chance = Chance.has_chance(self.player, 4)
        self.assertFalse(has_chance)

        self.player.chance_cards.append(4)
        has_chance = Chance.has_chance(self.player, 4)
        self.assertTrue(has_chance)

    # Test ability on_cooldown function
    def test_on_cooldown(self):

        # Check ability not on cooldown
        ability_id = 999
        cooldown = Ability.on_cooldown(self.player, ability_id)
        self.assertFalse(cooldown)

        # Check ability on cooldown
        self.player.cooldowns.append((ability_id, 2))
        cooldown = Ability.on_cooldown(self.player, ability_id)
        self.assertTrue(cooldown)

    # Test ability random_ability function
    def test_random_ability(self):

        self.assertEqual(self.player.rability, 0)
        Ability.random_ability(self.player)
        self.assertIsNot(self.player.rability, 0)

    # Test ability 01 Rejuvenation
    def test_ability01(self):

        correct_phase = Phases.POSTLUDE
        wrong_phase = Phases.PRELUDE

        ability_used = Ability.a_ability00(wrong_phase, self.player)
        self.assertFalse(ability_used)

        ability_used = Ability.a_ability00(correct_phase, self.player)
        self.assertTrue(ability_used)
        self.assertEqual(self.player.health, 1)

    # Test ability 02 Gentleman
    def test_ability02(self):

        correct_phase = Phases.POSTLUDE
        wrong_phase = Phases.PRELUDE

        ability_used = passive_map[1](wrong_phase, self.player)
        self.assertFalse(ability_used)

        ability_used = Ability.p_ability01(wrong_phase, self.player)
        self.assertFalse(ability_used)

        ability_used = Ability.p_ability01(correct_phase, self.player)
        self.assertFalse(ability_used)

        self.player.ddodged = 2
        ability_used = Ability.p_ability01(correct_phase, self.player)
        self.assertTrue(ability_used)
        self.assertEqual(len(self.player.chance_cards), 1)

    # Test ability 06 Attacker
    def test_ability06(self):

        correct_phase = Phases.POSTLUDE
        wrong_phase = Phases.PRELUDE

        ability_used = Ability.p_ability06(wrong_phase, self.player)
        self.assertFalse(ability_used)

        ability_used = Ability.p_ability06(correct_phase, self.player)
        self.assertFalse(ability_used)

        self.player.ddealt = 2
        ability_used = Ability.p_ability06(correct_phase, self.player)
        self.assertTrue(ability_used)
        self.assertEqual(len(self.player.chance_cards), 1)

    # Test ability 07 Critical
    def test_ability07(self):

        correct_phase = Phases.PRELUDE
        wrong_phase = Phases.POSTLUDE

        ability_used = Ability.a_ability07(wrong_phase, self.player)
        self.assertFalse(ability_used)

        ability_used = Ability.a_ability07(correct_phase, self.player)
        self.assertTrue(ability_used)

        self.assertEqual(self.player.modifier, 2)
        self.assertEqual(len(self.player.cooldowns), 1)


if __name__ == '__main__':
    unittest.main()
