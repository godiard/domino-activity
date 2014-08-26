#!/usr/bin/env python

# Piezas del domino
# By Gonzalo Odiard, 2006 godiard at gmail.com
# GPL License - http://www.gnu.org/copyleft/gpl.html


from gi.repository import Gdk
import cairo

from gettext import gettext as _

from sugar3.graphics import style

import cairoutils

# SIZE Es el ancho de una ficha (y la mitads del largo)
# podemos imaginar el tablero dividido en cuadrados de lado SIZE
SIZE = 60
# Si se quiere usar fichas mas grandes, se puede usar SIZE = 70 y
# cambiar _drawLabel el scale = 3

SCREEN_HEIGHT = Gdk.Screen.height() - style.GRID_CELL_SIZE
SCREEN_WIDTH = Gdk.Screen.width()


class Tile:

    """
    Informacion de cada posicion del tablero
    """

    UP = (0, -1)
    RIGHT = (1, 0)
    DOWN = (0, 1)
    LEFT = (-1, 0)

    def __init__(self, n, p):
        self.n = n
        self.p = p
        self.value = -1
        self.direction = (0, 0)
        # direction is a pair with the x, y increments where to put the next
        # tile. Then when we put the first tile, the start tile direction
        # will be (-1, 0) and the end tile direction will be (1, 0)
        # there are constants defined with the pairs


class DominoTableView():

    """
    Dibuja una grilla sobre la que se van a poner las fichas
    Ademas tiene metodos para saber a que casillero corresponde una
    posicion del mouse o donde ubicar una ficha
    """

    __gtype_name__ = 'DominoTableView'

    def __init__(self, **kwargs):
        self.cantX = int(SCREEN_WIDTH / SIZE)
        self.cantY = int((SCREEN_HEIGHT - SIZE * 4) / SIZE)
        self._margin_x = int((SCREEN_WIDTH - SIZE * self.cantX) / 2)
        self._margin_y = SIZE * 2

        self.top_player_position = SIZE / 4
        self.bottom_player_position = SCREEN_HEIGHT - SIZE * 2.10

        print "Table cantX", self.cantX, "cantY", self.cantY

    def show_values(self, ctx, tiles):
        """
        To debug: display the value in every tile off the table matrix
        """
        for n in range(0, self.cantX):
            for p in range(0, self.cantY):
                ctx.move_to(self._margin_x + n * SIZE + SIZE / 4,
                            self._margin_y + (p + 1) * SIZE)
                ctx.set_source_rgb(1, 0, 0)
                ctx.show_text(str(tiles[n][p].value))

    def mark_tile(self, ctx, tile):
        """
        To debug: used to show the position of the start and end tiles
        """
        ctx.set_source_rgb(0, 1, 0)
        ctx.set_line_width(3)
        ctx.rectangle(self._margin_x + tile.n * SIZE,
                      self._margin_y + tile.p * SIZE,
                      SIZE, SIZE)
        ctx.stroke()

    def get_tile_position(self, n, p):
        return self._margin_x + n * SIZE, self._margin_y + p * SIZE

    def msg_player_pass(self, ctx):
        ctx.save()
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL,
                             cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(30)
        text = _("Player pass, your turn...")
        x_bearing, y_bearing, width, height, x_advance, y_advance = \
            ctx.text_extents(text)
        x = (SCREEN_WIDTH - width) / 2
        y = SIZE * 1.8
        ctx.move_to(x, y)
        ctx.text_path(text)
        ctx.set_source_rgb(0, 0, 0)
        ctx.fill()
        ctx.restore()

    def msg_end_game(self, ctx, win):
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL,
                             cairo.FONT_WEIGHT_BOLD)
        text = ""
        ctx.set_font_size(40)
        if (win):
            text = _("You win!")
            face_filename = 'images/happy.png'
        else:
            text = _("You Lost")
            face_filename = 'images/sad.png'

        face_surf = cairo.ImageSurface.create_from_png(face_filename)

        x_bearing, y_bearing, width, height, x_advance, y_advance = \
            ctx.text_extents(text)

        piece_height = face_surf.get_height() + height * 4
        piece_width = piece_height * 2
        piece_radio = piece_height / 4

        # draw piece
        ctx.save()
        piece_x = (SCREEN_WIDTH - piece_width) / 2
        piece_y = (SCREEN_HEIGHT - piece_height) / 2
        cairoutils.draw_round_rect(
            ctx, piece_x, piece_y,
            piece_width, piece_height, piece_radio)
        ctx.set_source_rgb(0, 0, 0)
        ctx.fill_preserve()
        ctx.set_source_rgb(1, 1, 1)
        ctx.set_line_width(5)
        ctx.stroke()
        ctx.restore()

        # draw the face
        ctx.save()
        ctx.translate((SCREEN_WIDTH - face_surf.get_width()) / 2,
                      (piece_y + height))
        ctx.set_source_surface(face_surf)
        ctx.paint()
        ctx.restore()

        # draw text
        x = (SCREEN_WIDTH - width) / 2
        y = piece_y + face_surf.get_height() + height * 3
        ctx.move_to(x, y)
        ctx.text_path(text)
        ctx.set_source_rgb(1, 1, 1)
        ctx.fill()
