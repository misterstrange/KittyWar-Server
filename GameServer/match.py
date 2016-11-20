from network import Network
from enum import IntEnum
from threading import Lock


class RPFlags(IntEnum):

    SETUP = 0
    PRELUDE = 1
    ENACT_STRATS = 2
    POSTLUDE = 3

    READY = 99
    SELECT_CAT = 100
    USE_ABILITY = 101
    TARGET = 102


class AbilityFlags(IntEnum):

    Rejuvenation = 0
    Gentleman = 1


class Match:

    log_queue = None

    def __init__(self):

        self.lock = Lock()
        self.match_status = True

        self.phase = RPFlags.SETUP
        self.player1 = self.default_values()
        self.player2 = self.default_values()

    @staticmethod
    def default_values():
        return {'ready':  False, 'ddealt': 0, 'ddodged': 0,
                'rability': 0}

    def process_request(self, username, request):

        self.lock.aquire()

        player = self.get_player(username)
        phase_map[request['flag']](player, request)

        self.lock.release()
        return self.match_status

    def setup(self, player, request):

        flag = request['flag']
        if flag == RPFlags.SELECT_CAT:
            request_map[request](player, request)

        elif flag == RPFlags.READY:

            players_ready = self.player_ready(player)
            if players_ready:

                self.reset_ready()
                self.phase = RPFlags.PRELUDE
                self.gloria_prelude(player)

    def gloria_prelude(self, player):

        self.use_passive_ability(player, player['cat'])
        self.use_passive_ability(player, player['rability'])

    def prelude(self, player, request):

        flag = request['flag']
        if flag == RPFlags.USE_ABILITY:
            self.use_active_ability(player, request)

        elif flag == RPFlags.READY:

            players_ready = self.player_ready(player)
            if players_ready:

                self.reset_ready()
                self.phase = RPFlags.ENACT_STRATS

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

    def get_player(self, username):

        if self.player1['username'] == username:
            return self.player1
        else:
            return self.player2

    def player_ready(self, player):

        player['ready'] = True
        return self.player1['ready'] and self.player2['ready']

    def reset_ready(self):

        self.player1['ready'] = False
        self.player2['ready'] = False

    def select_cat(self, player, request):

        cat_id = Network.receive_data(player['connection'], request['size'])
        for cat in player['cats']:

            if cat == cat_id:

                player['cat'] = cat
                break

    def use_passive_ability(self, player, ability_id):

        useable = not self.on_cooldown(ability_id)
        if useable and ability_id in pability_map:
            pability_map[ability_id](self.phase, player)

    def use_active_ability(self, player, request):

        ability_id = Network.receive_data(player['connection'], request['size'])

        # Verify the ability is useable - the player has the ability and not on cooldown
        useable = ability_id == player['cat'] or ability_id == player['rability']
        useable = useable and not self.on_cooldown(ability_id)

        if useable and ability_id in aability_map:
            aability_map[ability_id](self.phase, player)

    # Checks if an ability is on cooldown
    def on_cooldown(self, ability_id):
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


# Ability 01 - Rejuvenation
def a_ability01(phase, player):

    if phase == RPFlags.POSTLUDE:
        # TODO
        pass


# Ability 02 - Gentleman
def p_ability02(phase, player):

    if phase == RPFlags.POSTLUDE:
        # TODO
        pass

aability_map = {
    AbilityFlags.Rejuvenation: a_ability01
}

pability_map = {
    AbilityFlags.Gentleman: p_ability02
}
