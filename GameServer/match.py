from network import Network
from enum import IntEnum
from threading import Lock
import random


class RPFlags(IntEnum):

    SETUP = 0
    PRELUDE = 1
    ENACT_STRATS = 2
    POSTLUDE = 3

    OP_CAT = 49
    GAIN_HP = 50
    OP_GAIN_HP = 51
    DMG_MODIFIED = 52
    OP_DMG_MODIFIED = 53
    GAIN_CHANCE = 54
    OP_GAIN_CHANCE = 55
    GAIN_ABILITY = 56

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


class Player:

    def __init__(self):

        self.connection = None
        self.username = None
        self.cats = None
        self.cat = None

        self.health = 0
        self.ddealt = 0
        self.ddodged = 0
        self.modifier = 1
        self.rability = None
        self.chance_cards = []
        self.cooldowns = []

        self.ready = False


class Match:

    log_queue = None

    def __init__(self):

        self.lock = Lock()
        self.match_valid = True

        self.phase = RPFlags.SETUP
        self.player1 = Player()
        self.player2 = Player()

    def process_request(self, username, request):

        if self.match_valid:

            player = self.get_player(username)
            phase_map[self.phase](player, request)

        return self.match_valid

    # Ends the match in an error
    def kill_match(self):

        self.match_valid = False
        self.alert_players(RPFlags.END_MATCH, 1, str(3))

    def disconnect(self, username):

        Match.log_queue.out(username + " has disconnected from the match")

        self.match_valid = False

        opponent = self.get_opponent(username)

        # The disconnected player gets a loss - notify the winning player
        response = Network.generate_responseb(RPFlags.END_MATCH, 1, str(1))
        Network.send_data(opponent, response)

    # Phase before prelude for handling match preparation
    def setup(self, player, request):

        flag = request.flag
        if flag == RPFlags.SELECT_CAT:
            request_map[request](player, request)

        elif flag == RPFlags.READY:

            # Set the player to ready and assign random ability
            players_ready = self.player_ready(player)
            self.random_ability(player)

            # If both players are ready proceed to the next phase
            if players_ready:

                # Set and alert players of next phase
                self.next_phase(RPFlags.PRELUDE)

                # Do not proceed if someone did not select a cat but readied up
                if self.player1.cat and self.player2.cat:
                    self.gloria_prelude()

                else:
                    self.kill_match()

    # Activates any prelude passive abilities the players have
    def gloria_prelude(self):

        Match.log_queue.put("Prelude phase starting for " + self.player1.username +
                            ", " + self.player2.username)

        self.use_passive_ability(self.player1, self.player1.cat)
        self.use_passive_ability(self.player1, self.player1.rability)

        self.use_passive_ability(self.player2, self.player2.cat)
        self.use_passive_ability(self.player2, self.player2.rability)

    def prelude(self, player, request):

        flag = request.flag
        if flag == RPFlags.USE_ABILITY:
            self.use_active_ability(player, request)

        elif flag == RPFlags.READY:

            players_ready = self.player_ready(player)
            if players_ready:

                # Set and alert players of next phase
                self.next_phase(RPFlags.ENACT_STRATS)
                self.gloria_enact_strats()

    def gloria_enact_strats(self):
        self.kill_match()

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

        if self.player1.username == username:
            return self.player1
        else:
            return self.player2

    # Returns the player that does not have the specified username
    def get_opponent(self, username):

        if self.player1.username == username:
            return self.player2
        else:
            return self.player1

    # Sends a message to both players with or without a body
    def alert_players(self, flag, size=None, body=None):

        # Check if there is a body to send
        if size is None:
            response = Network.generate_responseh(flag, 0)

        else:
            response = Network.generate_responseb(flag, size, body)

        Network.send_data(self.player1.connection, response)
        Network.send_data(self.player2.connection, response)

    # Gives and notifies a user of their random ability for the match
    def random_ability(self, player):

        ability_id = random.randrange(6, 8)
        player.rability = ability_id

        Match.log_queue.put(player.name + " received random ability: " + ability_id)

        response = Network.generate_responseb(RPFlags.GAIN_ABILITY, 1, str(ability_id))
        Network.send_data(player.connection, response)

    # Move onto the next phase specified and alert the players
    def next_phase(self, phase):

        self.reset_ready()
        self.phase = phase
        self.alert_players(RPFlags.NEXT_PHASE)

    # Set a player to ready and return whether both are ready or not
    def player_ready(self, player):

        player.ready = True
        return self.player1.ready and self.player2.ready

    # Sets both players to not ready
    def reset_ready(self):

        self.player1.ready = False
        self.player2.ready = False

    # Handles the user selecting a cat for the match
    def select_cat(self, player, request):

        # Prepare response and retrieve cat the client wants to use
        response = Network.generate_responseh(RPFlags.SELECT_CAT, 1)
        cat_id = Network.receive_data(player.connetion, request.size)

        # Verify user can select the cat they have
        valid_cat = False
        for cat in player.cats:

            if cat['ability_id'] == cat_id:

                Match.log_queue.put(player.username + " has selected their cat" +
                                    " - id: " + str(cat))

                player.cat = cat_id
                player.health = cat['health']
                valid_cat = True
                response.append(1)
                break

        # Check if previous selection was valid
        # If a cat the user does not have is selected the match is ended immediately
        # Code 3 is used - No winner match ending in error
        if not valid_cat:

            Match.log_queue.put("Illegal cat selection from " +
                                player.username + ", ending match with error status")

            self.match_valid = False
            self.alert_players(RPFlags.END_MATCH, 1, str(3))
            return

        # Notify player selection was successful and notify opponent of your cat
        Network.send_data(player.connection, response)

        response = Network.generate_responseb(RPFlags.OP_CAT, 1, str(player.cat))
        opponent = self.get_opponent(player.username)
        Network.send_data(opponent.connection, response)

    def use_passive_ability(self, player, ability_id):

        useable = not self.on_cooldown(player, ability_id)

        ability_responses = None
        if useable and is_passive(ability_id):

            Match.log_queue.put(player.username +
                                " using passive ability - id: " + ability_id)
            ability_responses = pability_map[ability_id](self.phase, player)

        if ability_responses:

            Network.send_data(player.connection, ability_responses[0])
            if len(ability_responses) > 1:
                opponent = self.get_opponent(player.username)
                Network.send_data(opponent.connection, ability_responses[1])

    def use_active_ability(self, player, request):

        # Prepare response based on the ability being used or not
        response = Network.generate_responseh(RPFlags.USE_ABILITY, 1)

        ability_id = Network.receive_data(player.connection, request.size)

        # Verify the ability is useable - the player has the ability and not on cooldown
        useable = ability_id == player.cat or ability_id == player.rability
        useable = useable and not self.on_cooldown(player, ability_id)

        ability_responses = None
        if useable and is_active(ability_id):

            Match.log_queue.put(player.username +
                                " using active ability - id: " + ability_id)
            ability_responses = aability_map[ability_id](self.phase, player)
            response.append(1)

        else:
            response.append(0)

        Network.send_data(player.connection, response)
        if ability_responses:

            Network.send_data(player.connection, ability_responses[0])
            if len(ability_responses) > 1:
                opponent = self.get_opponent(player.username)
                Network.send_data(opponent.connection, ability_responses[1])

    # Checks if an ability is on cooldown
    def on_cooldown(self, player, ability_id):

        cd = False
        for cooldown in player.cooldowns:

            if cooldown[0] == ability_id:
                cd = True
                break

        return cd


phase_map = {

    RPFlags.SETUP: Match.setup,
    RPFlags.PRELUDE: Match.prelude,
    RPFlags.ENACT_STRATS: Match.enact_strats,
    RPFlags.POSTLUDE: Match.postlude
}

request_map = {

    RPFlags.SELECT_CAT: Match.select_cat
}


# Returns true if the ability is an active ability
def is_active(ability_id):
    return ability_id in aability_map


# Returns true if the ability is a passive ability
def is_passive(ability_id):
    return ability_id in pability_map


# Ability 01 - Rejuvenation
# Gain 1 HP - Postlude - Cooldown: 2
def a_ability01(phase, player):

    if phase == RPFlags.POSTLUDE:

        player.health += 1
        player.cooldowns.apppend((AbilityFlags.Rejuvenation, 3))

        Match.log_queue.put(player.name + " used Rejuvenation +1 Health Point")

    ability_responses = [

        Network.generate_responseb(RPFlags.GAIN_HP, 1, str(1)),
        Network.generate_responseb(RPFlags.OP_GAIN_HP, 1, str(1))
    ]

    return ability_responses


# Ability 07 - Critical Hit
# Modifier x2 - PRELUDE - Cooldown: 2
def a_ability07(phase, player):

    if phase == RPFlags.PRELUDE:

        player.modifier *= 2
        player.cooldowns.append((AbilityFlags.Critical, 3))

        Match.log_queue.put(player.name + " used Critical Hit 2x Damage")

    ability_responses = [

        Network.generate_responseb(RPFlags.DMG_MODIFIED, 1, str(player.modifier)),
        Network.generate_responseb(RPFlags.OP_DMG_MODIFIED, 1, str(player.modifier))
    ]

    return ability_responses


# Ability 02 - Gentleman
# chance gained on condition - POSTLUDE
# condition: damage dodged >= 2
def p_ability02(phase, player):

    ability_responses = None
    if phase == RPFlags.POSTLUDE:
        if player.ddodged >= 2:

            chance_card = random.randrange(0, 9)
            player.chance_cards.append(chance_card)

            Match.log_queue.put(player.name + " used Gentleman +1 Chance Card")

            ability_responses.append(
                Network.generate_responseb(RPFlags.GAIN_CHANCE, 1, str(chance_card)))
            ability_responses.append(
                Network.generate_responseb(RPFlags.OP_GAIN_CHANCE, 1, str(chance_card)))

    return ability_responses


# Ability 06 - Attacker
# chance gained on condition - POSTLUDE
# condition: damage dealt >= 2
def p_ability06(phase, player):

    ability_responses = None
    if phase == RPFlags.POSTLUDE:
        if player.ddealt >= 2:

            chance_card = random.randrange(0, 9)
            player.chance_cards.append(chance_card)

            Match.log_queue.put(player.name + " used Attacker +1 Chance Card")

            ability_responses.append(
                Network.generate_responseb(RPFlags.GAIN_CHANCE, 1, str(chance_card)))
            ability_responses.append(
                Network.generate_responseb(RPFlags.OP_GAIN_CHANCE, 1, str(chance_card)))

    return ability_responses

aability_map = {

    AbilityFlags.Rejuvenation: a_ability01,
    AbilityFlags.Critical: a_ability07
}

pability_map = {

    AbilityFlags.Gentleman: p_ability02,
    AbilityFlags.Attacker: p_ability06
}
