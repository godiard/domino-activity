#!/usr/bin/env python

# Piezas del domino
# By Gonzalo Odiard, 2006 godiard at gmail.com
# GPL License - http://www.gnu.org/copyleft/gpl.html

from sugar3.graphics import style
import dominoview
import cairoutils


def _luminance(color):
    ''' Calculate luminance value '''
    return int(color[1:3], 16) * 0.3 + int(color[3:5], 16) * 0.6 + \
        int(color[5:7], 16) * 0.1


def lighter_color(colors):
    ''' Which color is lighter?
            colors: array of str with two colors in #rrggbb format
            returns index of the color in the array
    '''
    if _luminance(colors[0]) > _luminance(colors[1]):
        return 0
    return 1


def darker_color(colors):
    ''' Which color is darker?
            colors: array of str with two colors in #rrggbb format
            returns index of the color in the array
    '''
    return 1 - lighter_color(colors)


class DominoPiece:
    """ Informacion de cada pieza del juego (visible o no) """

    PIECE_PLAYER = 1
    PIECE_IN_MOVE = 2
    PIECE_PLACED = 3
    PIECE_WAITING = 0

    def __init__(self, a, b):
        # print "creando pieza",n,p

        self.a = a
        self.b = b
        self.textA = str(a)
        self.textB = str(b)
        self.vertical = False
        self.reversed = False
        self.player = None
        self.state = DominoPiece.PIECE_WAITING
        self.visible = False
        self._itemA = None
        self._itemB = None

    def check_touched(self, x, y):
        # check if the x, y position touch the piece
        if self.vertical:
            width = dominoview.SIZE
            height = dominoview.SIZE * 2
        else:
            width = dominoview.SIZE * 2
            height = dominoview.SIZE
        return (self.x < x < self.x + width) and (self.y < y < self.y + height)

    def draw(self, ctx, selected, fipped=False):
        SIZE = dominoview.SIZE
        if fipped:
            SIZE = SIZE * 0.75

        ctx.save()
        ctx.translate(self.x, self.y)
        ctx.move_to(self.x, self.y)
        ctx.set_line_width(3)
        r = dominoview.SIZE / 3
        stroke_r, stroke_g, stroke_b = 0.9, 0.9, 0.9
        fill_r, fill_g, fill_b = 1, 1, 1
        alpha = 1
        if self.player.color is not None:
            xocolor = self.player.color
            stroke_r, stroke_g, stroke_b, alpha = style.Color(
                xocolor.get_stroke_color(), 1.0).get_rgba()
            fill_r, fill_g, fill_b, alpha = style.Color(
                xocolor.get_fill_color(), 1.0).get_rgba()
            if selected:
                fill_r, fill_g, fill_b = 1, 1, 1
                my_colors = [xocolor.get_stroke_color(),
                             xocolor.get_fill_color()]
                darker_color_str = my_colors[darker_color(my_colors)]
                stroke_r, stroke_g, stroke_b, alpha = style.Color(
                    darker_color_str).get_rgba()

        if self.vertical:

            cairoutils.draw_round_rect(ctx, 0, 0, SIZE, SIZE * 2, r)
            ctx.set_source_rgb(fill_r, fill_g, fill_b)
            ctx.fill_preserve()
            ctx.set_source_rgb(stroke_r, stroke_g, stroke_b)
            ctx.stroke()

            if not fipped:

                ctx.move_to(SIZE / 5, SIZE)
                ctx.line_to(SIZE / 5 * 4, SIZE)
                ctx.set_source_rgb(stroke_r, stroke_g, stroke_b)
                ctx.stroke()

                if not self.reversed:
                    self._draw_label_a(ctx, 0, 0)
                    self._draw_label_b(ctx, 0, SIZE)
                else:
                    self._draw_label_b(ctx, 0, 0)
                    self._draw_label_a(ctx, 0, SIZE)

        else:
            cairoutils.draw_round_rect(ctx, 0, 0, SIZE * 2, SIZE, r)
            ctx.set_source_rgb(fill_r, fill_g, fill_b)
            ctx.fill_preserve()
            ctx.set_source_rgb(stroke_r, stroke_g, stroke_b)
            ctx.stroke()

            if not fipped:

                ctx.move_to(SIZE, SIZE / 5)
                ctx.line_to(SIZE, SIZE / 5 * 4)
                ctx.set_source_rgb(stroke_r, stroke_g, stroke_b)
                ctx.stroke()

                if not self.reversed:
                    self._draw_label_a(ctx, 0, 0)
                    self._draw_label_b(ctx, SIZE, 0)
                else:
                    self._draw_label_b(ctx, 0, 0)
                    self._draw_label_a(ctx, SIZE, 0)

        ctx.restore()

    def _draw_label_a(self, ctx, x, y):
        self.player.game.processor.draw_label(ctx, self, self.textA, x, y)

    def _draw_label_b(self, ctx, x, y):
        self.player.game.processor.draw_label(ctx, self, self.textB, x, y)
