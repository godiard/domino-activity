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
    }

    # estados del juego
    GAME_STATE_SELECT_PIECE = 1
    GAME_STATE_LOCATE_PIECE = 2
    GAME_STATE_ANOTHER_USER = 3
    GAME_STATE_FINISH_GAME = 4

    def __init__(self, processor):
        GObject.GObject.__init__(self)
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

    def next_player(self, num_player):
        logging.debug('START n %s p %s direction %s value %s', self.start.n,
                      self.start.p, self.start.direction, self.start.value)
        logging.debug('END n %s p %s direction %s value %s', self.end.n,
                      self.end.p, self.end.direction, self.end.value)

        if num_player >= len(self.players) - 1:
            return self.players[0]
        else:
            return self.players[num_player + 1]

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

    def request_one_piece(self):
        self.emit('piece-placed')
        return self.take_pieces(1)

    def test_free_position(self, n, p):
        logging.debug('test_free_position %s %s', n, p)
        if (n < 0) or (p < 0) or (n > self.cantX) or (p > self.cantY):
            # Out of limits
            logging.debug('Out of limits cantX %s catY %s',
                          self.cantX, self.cantY)
            return False
        try:
            if self.values[n][p].value != -1:
                # N,P position have a piece
                logging.debug('Tile busy n %s p %s', n, p)
                return False
        except IndexError:
            return False
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
        for n in range(1, numPlayers):
            player = DominoPlayer(self, n)
            player.set_pieces(self.take_pieces(7))
            self.players.append(player)

        # comienza a jugar el primer jugador
        self.players[0].play()
        self.ui_player = self.players[1]
        self.ui_player.color = profile.get_color()
        self.ui_player.name = profile.get_nick_name()

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
