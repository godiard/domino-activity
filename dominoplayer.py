from gettext import gettext as _
import random

from gi.repository import GObject

from dominoview import Tile
from dominopiece import DominoPiece


class DominoPlayer:

    """
    Jugadores (automaticos o humanos) del domino
    """

    def __init__(self, game, number):
        self.number = number
        self.name = _('Player ')+str(self.number)
        self.game = game
        self._pieces = []
        self.order_piece_selected = 0
        self.playing = False
        self.color = None
        # se usa para saber si este usuario paso la ultima vuelta
        self.has_passed = False
        # where are displayed the pieces for this player
        self.pieces_position = self.game.table.second_player_position

    def set_pieces(self, pieces):
        self._pieces = pieces
        for piece in self._pieces:
            piece.player = self
            piece.state = DominoPiece.PIECE_PLAYER
        self.order_piece_selected = 0

    def get_pieces(self):
        return self._pieces

    def play(self):
        # "Play player",self.number
        self.playing = True
        # "Cant piezas",len(self._pieces)
        if self == self.game.ui_player:
            # "Abilitando botones"
            self.game.game_state = self.game.GAME_STATE_SELECT_PIECE

    def end_play(self):
        # "End player",self.number
        self.playing = False
        self.game.player_ended(self.number)

    def remove_piece(self, piece):
        cantPieces = len(self._pieces)
        # TODO: there are a better way?
        for n in range(0, len(self._pieces)):
            p = self._pieces[n]
            if piece == p:
                self._pieces[n] = cantPieces
                self._pieces.remove(cantPieces)
                return

    def test_good_position(self, tile, piece):
        n, p = tile.n, tile.p
        # logging.error('tile value %s direction %s piece a %s piece b %s',
        #               tile.value, tile.direction, piece.a, piece.b)
        # check using the tile direction if the next 2 spaces are free
        ok = True
        for i in range(0, 2):
            n = n + tile.direction[0]
            p = p + tile.direction[1]
            if not self.game.test_free_position(n, p):
                ok = False
                break

        # check a 3 tile in the same direction
        # can be out of the table, but can't be busy
        n3 = n + tile.direction[0]
        p3 = p + tile.direction[1]
        if not self.game.test_out_or_free_position(n3, p3):
            ok = False

        if ok:
            # logging.error('3 spaces free')
            # define piece position
            # logging.error('piece position n %s, p %s', n, p)
            # get the minimal between the original tile + 1 and
            # the final n, p values calculated
            ori_n = tile.n + tile.direction[0]
            ori_p = tile.p + tile.direction[1]
            min_n, min_p = min(n, ori_n), min(p, ori_p)
            # logging.error('piece position n %s, p %s', min_n, min_p)

            # logging.error('tile.value %s piece a %s b %s direction %s',
            #               tile.value, piece.a, piece.b, tile.direction)
            # define piece orientation
            if tile.value == piece.b:
                if tile.direction in (Tile.RIGHT, Tile.DOWN):
                    piece.reversed = True
                new_value = piece.a
            elif tile.value == piece.a:
                if tile.direction in (Tile.LEFT, Tile.UP):
                    piece.reversed = True
                new_value = piece.b
            piece.vertical = tile.direction in (Tile.DOWN, Tile.UP)
            # logging.error('test_good_position vertical %s reversed %s',
            #               piece.vertical, piece.reversed)
            return new_value, tile.direction, piece, min_n, min_p
        else:
            # rotate the tile direction
            if tile.direction == Tile.LEFT:
                tile.direction = Tile.UP
            elif tile.direction == Tile.UP:
                tile.direction = Tile.RIGHT
            elif tile.direction == Tile.RIGHT:
                tile.direction = Tile.DOWN
            elif tile.direction == Tile.DOWN:
                tile.direction = Tile.LEFT
            return self.test_good_position(tile, piece)

    def place_piece(self, piece):
        start_value = self.game.start.value
        end_value = self.game.end.value
        ends = [self.game.start, self.game.end]

        if (piece.a == start_value and piece.b == end_value) or \
                (piece.a == end_value and piece.b == start_value):
            # if the piece can be put in any end, select a end where
            # you have more posibilities
            # create a dict with the values in my other pieces and how many
            # pieces have that value
            values = {}
            for p in self._pieces:
                if p != piece:
                    if p.a in values:
                        values[p.a] = values[p.a] + 1
                    else:
                        values[p.a] = 1
                    if p.b in values:
                        values[p.b] = values[p.b] + 1
                    else:
                        values[p.b] = 1
            if piece.a not in values:
                values[piece.a] = 0
            if piece.b not in values:
                values[piece.b] = 0

            # compare how many values have to put after this piece
            if values[piece.a] > values[piece.b]:
                # attach piece.b
                if piece.b == start_value:
                    ends = [self.game.start]
                else:
                    ends = [self.game.end]
            else:
                # attach piece.a
                if piece.a == start_value:
                    ends = [self.game.start]
                else:
                    ends = [self.game.end]

        for end in ends:
            if piece.a == end.value or piece.b == end.value:
                # try with start tile
                new_tile_value, direction, piece, piece_n, piece_p = \
                    self.test_good_position(end, piece)
                self.game.put_piece(self, piece, piece_n, piece_p)
                end.value = new_tile_value
                end.n += direction[0] * 2
                end.p += direction[1] * 2
                end.direction = direction
                return True

        return False


class SimpleAutoPlayer(DominoPlayer):

    """
    Jugador automatico simple
    Busca la primera ficha que pueda ubicarse en alguna de las posiciones
    si no encuentra una pide
    NO TIENE NINGUNA ESTRATEGIA
    """

    def __init__(self, game, number):
        DominoPlayer.__init__(self, game, number)
        self.pieces_position = self.game.table.first_player_position

    def play(self):
        if self.game.is_finished():
            return False
        # "Jugando automatico"
        if self.game.start is None:
            # si no hay ninguna pieza en el tablero ponemos la primera
            piece = self._pieces[0]
            n, p = self.game.cantX / 2 - 1, self.game.cantY / 2
            self.game.put_piece(self, piece, n, p)

            # seteamos comienzo y fin del domino
            startTile = Tile(n, p)
            startTile.value = piece.a
            startTile.direction = Tile.LEFT
            self.game.start = startTile

            endTile = Tile(n + 1, p)
            endTile.value = piece.b
            endTile.direction = Tile.RIGHT
            self.game.end = endTile

        else:
            # "automatica siguiente"
            # buscamos si tenemos alguna ficha que corresponda
            # en el comienzo
            if not self.check_put_piece():
                # pido una hasta que sea valida o no hayan mas disponibles
                # si no encontramos pedimos hasta que alguna sirva
                # "Pido pieza"
                if self.game.request_one_piece(self):
                    if self.game.ENABLE_AUTO_MODE:
                        GObject.timeout_add(300, self.play)
                    else:
                        GObject.timeout_add_seconds(1, self.play)
                    return False
                else:
                    self.has_passed = True

        # juega el siguiente jugador
        GObject.idle_add(self.end_play)
        return False

    def check_put_piece(self):
        # use random to balance what end check first
        if random.random() > .5:
            ends = (self.game.start, self.game.end)
        else:
            ends = (self.game.end, self.game.start)

        for tile in ends:
            # look for a piece with the value
            piece = self._get_piece_with_value(tile.value)
            if piece is not None:
                self.place_piece(piece)
                return True
        return False

    # elige una pieza que tenga un valor
    def _get_piece_with_value(self, value):
        for piece in self._pieces:
            if piece.player == self:
                # "get_piece_with_value",piece.a, piece.b
                if (piece.a == value) or (piece.b == value):
                    return piece
        return None
