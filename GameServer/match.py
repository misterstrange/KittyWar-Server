from network import Network
from enum import IntEnum
from threading import Lock
import random


class RPFlags(IntEnum):

    SETUP = 0
    PRELUDE = 1
    ENACT_STRATS = 2
    POSTLUDE = 3

    END_MATCH = 9
    NEXT_PHASE = 98
    READY = 99
    SELECT_CAT = 100
    USE_ABILITY = 101
    TARGET = 102


class AbilityFlags(IntEnum):

    Rejuvenation = 0
    Gentleman = 1
    Attacker = 6
    Critical = 7


class Match:

    log_queue = None

    def __init__(self):

        self.lock = Lock()
        self.match_valid = True

        self.phase = RPFlags.SETUP
        self.player1 = self.default_values()
        self.player2 = self.default_values()

    @staticmethod
    def default_values():

        rand_ability = random.randrange(6, 8)
        return {'ready':  False, 'cat': None, 'ddealt': 0, 'ddodged': 0,
                'health': 0, 'rability': rand_ability, 'cooldowns': []}

    def process_request(self, username, request):

        if self.match_valid:
            player = self.get_player(username)
            phase_map[self.phase](player, request)

        return self.match_valid

    # Sends a message to both players with or without a body
    def alert_players(self, flag, size=None, body=None):

        # Check if there is a body to send
        if size is None:
            response = Network.generate_responseh(flag, 0)
        else:
            response = Network.generate_responseb(flag, size, body)

        Network.send_data(self.player1['connection'], response)
        Network.send_data(self.player2['connection'], response)

    # Phase before prelude for handling match preparation
    def setup(self, player, request):

        flag = request['flag']
        if flag == RPFlags.SELECT_CAT:
            request_map[request](player, request)

        elif flag == RPFlags.READY:

            players_ready = self.player_ready(player)
            if players_ready:

                self.next_phase(RPFlags.PRELUDE)
                self.gloria_prelude(player)

    # Activates any prelude passive abilities the players have
    def gloria_prelude(self, player):

        Match.log_queue.put("Prelude phase starting for " + self.player1['username'] +
                            ", " + self.player2['username'])

        self.use_passive_ability(player, player['cat'])
        self.use_passive_ability(player, player['rability'])

    def prelude(self, player, request):

        flag = request['flag']
        if flag == RPFlags.USE_ABILITY:
            self.use_active_ability(player, request)

        elif flag == RPFlags.READY:

            players_ready = self.player_ready(player)
            if players_ready:
                self.next_phase(RPFlags.ENACT_STRATS)

    def enact_strats(self, player, request):
        pass

    def show_cards(self):
        pass

    def settle_strats(self):
        pass

    def gloria_postlude(self):
        pass

    def postlude(self):
        pass

    # Returns player one or two based on username
    def get_player(self, username):

        if self.player1['username'] == username:
            return self.player1
        else:
            return self.player2

    # Move onto the next phase specified
    def next_phase(self, phase):

        self.reset_ready()
        self.phase = phase
        self.alert_players(RPFlags.NEXT_PHASE)

    # Set a player to ready and return whether both are ready or not
    def player_ready(self, player):

        player['ready'] = True
        return self.player1['ready'] and self.player2['ready']

    # Sets both players to not ready
    def reset_ready(self):

        self.player1['ready'] = False
        self.player2['ready'] = False

    # Handles the user selecting a cat for the match
    def select_cat(self, player, request):

        # Prepare response and retrieve cat the client wants to use
        response = Network.generate_responseh(RPFlags.SELECT_CAT, 1)
        cat_id = Network.receive_data(player['connection'], request['size'])

        # Verify user can select the cat they have
        valid_cat = False
        for cat in player['cats']:

            if cat == cat_id:

                Match.log_queue.put(player['username'] + " has selected their cat" +
                                    " - id: " + str(cat))

                player['cat'] = cat_id
                valid_cat = True
                response.append(1)
                break

        # Check if previous selection was valid
        # If a cat the user does not have is selected the match is ended immediately
        # Code 3 is used - No winner match ending in error
        if not valid_cat:

            Match.log_queue.put("Illegal cat selection from " +
                                player['username'] + ", ending match with error status")

            self.match_valid = False
            self.alert_players(RPFlags.END_MATCH, 1, str(3))
            return

        Network.send_data(player['connection'], response)

    def use_passive_ability(self, player, ability_id):

        useable = not self.on_cooldown(ability_id)
        if useable and is_passive(ability_id):

            Match.log_queue.put(player['username'] +
                                " using passive ability - id: " + ability_id)
            pability_map[ability_id](self.phase, player)

    def use_active_ability(self, player, request):

        ability_id = Network.receive_data(player['connection'], request['size'])

        # Verify the ability is useable - the player has the ability and not on cooldown
        useable = ability_id == player['cat'] or ability_id == player['rability']
        useable = useable and not self.on_cooldown(ability_id)

        if useable and is_active(ability_id):

            Match.log_queue.put(player['username'] +
                                " using active ability - id: " + ability_id)
            aability_map[ability_id](self.phase, player)

    # Checks if an ability is on cooldown
    def on_cooldown(self, ability_id):
        # TODO
        return True


phase_map = {

    RPFlags.SETUP: Match.setup,
    RPFlags.PRELUDE: Match.prelude,
    RPFlags.ENACT_STRATS: Match.enact_strats,
    RPFlags.POSTLUDE: Match.postlude
}

request_map = {

    RPFlags.SELECT_CAT: Match.select_cat
}


def is_active(ability_id):
    return ability_id in aability_map


def is_passive(ability_id):
    return ability_id in pability_map


# Ability 01 - Rejuvenation
def a_ability01(phase, player):

    if phase == RPFlags.POSTLUDE:
        # TODO
        pass


# Ability 07 - Critical Hit
def a_ability07(phase, player):

    if phase == RPFlags.PRELUDE:
        # TODO
        pass


# Ability 02 - Gentleman
def p_ability02(phase, player):

    if phase == RPFlags.POSTLUDE:
        # TODO
        pass


# Ability 06 - Attacker
def p_ability06(phase, player):

    if phase == RPFlags.POSTLUDE:
        # TODO
        pass

aability_map = {

    AbilityFlags.Rejuvenation: a_ability01,
    AbilityFlags.Critical: a_ability07
}

pability_map = {

    AbilityFlags.Gentleman: p_ability02,
    AbilityFlags.Attacker: p_ability06
}
