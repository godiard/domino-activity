import random
import logging

from gi.repository import GObject

from sugar3 import profile

from dominopiece import DominoPiece
import dominoview
from dominoview import Tile
from dominoview import DominoTableView
from dominoplayer import DominoPlayer
from dominoplayer import SimpleAutoPlayer


class DominoGame(GObject.GObject):

    """
    Esta es la clase principal del juego
    """

    __gsignals__ = {
        'piece-placed': (GObject.SignalFlags.RUN_FIRST, None, []),
        'player-ended': (GObject.SignalFlags.RUN_FIRST, None, []),
    }

    # estados del juego
    GAME_STATE_SELECT_PIECE = 1
    GAME_STATE_LOCATE_PIECE = 2
    GAME_STATE_ANOTHER_USER = 3
    GAME_STATE_FINISH_GAME = 4

    def __init__(self, processor):
        GObject.GObject.__init__(self)

        # TO DEBUG you can set this variable on True
        # and make the computer play against himself.
        self.ENABLE_AUTO_MODE = False

        self.ui_player = None
        self.table = DominoTableView()
        self.pieces = []
        self.placed_pieces = []
        self.game_state = DominoGame.GAME_STATE_SELECT_PIECE
        self.players = []
        self.values = []
        self.cantX = self.table.cantX
        self.cantY = self.table.cantY
        for n in range(0, self.cantX):
            self.values.append([])
            for p in range(0, self.cantY):
                tile = Tile(n, p)
                self.values[n].append(tile)
        # primera y ultima posicion de las piezas
        self.start = None
        self.end = None

        self.processor = processor
        self.winner = None
        self._actual_player = 0

    def next_player(self, num_player):
        if num_player >= len(self.players) - 1:
            return self.players[0]
        else:
            return self.players[num_player + 1]

    def player_ended(self, num_player):
        self._actual_player = num_player
        player = self.players[num_player]
        end_game, win = self._verify_end_of_game(player)
        if end_game:
            self.game_state = DominoGame.GAME_STATE_FINISH_GAME
            if win:
                self.winner = player
            else:
                self.winner = self.next_player(num_player)
        self.emit('player-ended')

    def player_automatic_passed(self):
        return self._actual_player == 0 and \
            self.players[0].has_passed

    def player_automatic_playing(self):
        return self._actual_player == 0

    def _verify_end_of_game(self, player):
        end_game = False
        player_win = False

        if len(player.get_pieces()) == 0:
            return True, True

        # Chequeo si todos los jugadores pasaron

        all_has_passed = True
        for p in self.players:
            if not p.has_passed:
                all_has_passed = False
        logging.error('all_has_passed %s', all_has_passed)
        # si todos pasaron veo quien tiene menos fichas
        if all_has_passed:
            if len(self.players[0].get_pieces()) == \
                    len(self.players[1].get_pieces()):
                # both player have same number of pieces
                # win second player
                logging.error('both player have same number of pieces')
                player_win = player != self.players[0]
            else:
                min_cant_pieces = 100
                player_with_minus_pieces = None
                for p in self.players:
                    if len(p.get_pieces()) < min_cant_pieces:
                        logging.error('minimum')
                        min_cant_pieces = len(p.get_pieces())
                        player_with_minus_pieces = p

                player_win = player_with_minus_pieces == player

            end_game = True

        return end_game, player_win

    def start_next_player(self):
        self.next_player(self._actual_player).play()
        return False

    def is_finished(self):
        return self.game_state == DominoGame.GAME_STATE_FINISH_GAME

    # Posiciona una pieza en el tablero
    def put_piece(self, player, piece, n, p):
        player.remove_piece(piece)

        valueA = piece.a
        valueB = piece.b
        if piece.reversed:
            valueA = piece.b
            valueB = piece.a

        self.values[n][p].value = valueA
        if piece.vertical:
            self.values[n][p + 1].value = valueB
        else:
            self.values[n + 1][p].value = valueB

        piece.state = DominoPiece.PIECE_PLACED
        piece.visible = True
        piece.x, piece.y = self.table.get_tile_position(n, p)
        self.placed_pieces.append(piece)
        player.order_piece_selected = 0
        player.has_passed = False
        self.emit('piece-placed')

    def request_one_piece(self, player):
        pieces = self.take_pieces(1)
        if len(pieces) > 0:
            piece = pieces[0]
            piece.player = player
            piece.state = DominoPiece.PIECE_PLAYER
            player.get_pieces().append(piece)
            self.emit('piece-placed')
            return True
        else:
            return False

    def test_free_position(self, n, p):
        # logging.debug('test_free_position %s %s', n, p)
        if (n < 0) or (p < 0) or (n > self.cantX) or (p > self.cantY):
            # Out of limits
            # logging.debug('Out of limits cantX %s catY %s',
            #               self.cantX, self.cantY)
            return False
        try:
            if self.values[n][p].value != -1:
                # N,P position have a piece
                # logging.debug('Tile busy n %s p %s', n, p)
                return False
        except IndexError:
            return False
        return True

    def test_out_or_free_position(self, n, p):
        # logging.debug('test_free_position %s %s', n, p)
        if (n < 0) or (p < 0) or (n > self.cantX) or (p > self.cantY):
            # Out of limits
            # logging.debug('Out of limits cantX %s catY %s',
            #               self.cantX, self.cantY)
            return True
        try:
            if self.values[n][p].value != -1:
                # N,P position have a piece
                # logging.debug('Tile busy n %s p %s', n, p)
                return False
        except IndexError:
            return True
        return True

    def _create_domino(self):
        for n in range(0, 7):
            for p in range(n, 7):
                # creo pieza
                piece = DominoPiece(n, p)
                self.pieces.append(piece)
        self.processor.alter_labels(self.pieces)

    # Toma al azar una cantidad de piezas del juego y
    # las devuelve en una coleccion
    def take_pieces(self, cant):
        result = []
        for n in range(0, cant):
            cantPieces = len(self.pieces)
            if cantPieces > 0:
                r = int(random.random() * cantPieces)
                piece = self.pieces[r]
                # la quito de las piezas del juego
                self.pieces[r] = cantPieces
                self.pieces.remove(cantPieces)
                # la agrego a result
                result.append(piece)
        return result

    # para debug
    def print_value_pieces(self, pieceList):
        for piece in pieceList:
            logging.error('%s %s', piece.n, piece.p)

    def start_game(self, numPlayers):
        self._create_domino()
        self.placed_pieces = []
        self.players = []
        auto_player = SimpleAutoPlayer(self, 0)
        auto_player.set_pieces(self.take_pieces(7))
        self.players.append(auto_player)

        if self.ENABLE_AUTO_MODE:
            auto_player2 = SimpleAutoPlayer(self, 1)
            auto_player2.set_pieces(self.take_pieces(7))
            auto_player2.pieces_y_position = self.table.bottom_player_position
            self.players.append(auto_player2)
        else:
            for n in range(1, numPlayers):
                player = DominoPlayer(self, n)
                player.set_pieces(self.take_pieces(7))
                self.players.append(player)

        # comienza a jugar el primer jugador
        self.players[0].play()
        self.ui_player = self.players[1]
        self.ui_player.color = profile.get_color()
        self.ui_player.name = profile.get_nick_name()
        self._actual_player = 0

    def show_pieces_player(self, player):
        pieces = player.get_pieces()

        if len(pieces) > 0:
            separacion_x = int((dominoview.SCREEN_WIDTH - dominoview.SIZE *
                               len(pieces)) / len(pieces))
            x = separacion_x / 2
            y = player.pieces_y_position

            for piece in pieces:
                piece.x = x
                piece.y = y
                piece.vertical = True

                x = x + dominoview.SIZE + separacion_x
                piece.visible = True


class DominoGamePoints:

    def __init__(self):
        self.name = None
        self.played = 0
        self.win = 0
        self.lost = 0
