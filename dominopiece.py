#!/usr/bin/env python

# Piezas del domino
# By Gonzalo Odiard, 2006 godiard at gmail.com
# GPL License - http://www.gnu.org/copyleft/gpl.html

from sugar3.graphics import style
import dominoview
import cairoutils


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

    def draw(self, ctx, selected):
        SIZE = dominoview.SIZE
        # if self.vertical:
        #   width = SIZE + SIZE/8 + 2
        #   height = SIZE*2 + SIZE/8 + 2
        # else:
        #   width = SIZE*2 + SIZE/8 + 2
        #   height = SIZE + SIZE/8 + 2

        ctx.save()
        ctx.translate(self.x, self.y)
        ctx.move_to(self.x, self.y)
        # ctx.translate(1,1)
        # ctx.move_to(1, 1)
        r = 10
        stroke_r, stroke_g, stroke_b = 0, 0, 0
        fill_r, fill_g, fill_b = 1, 1, 1
        alpha = 1
        if self.player.color is not None:
            xocolor = self.player.color
            stroke_r, stroke_g, stroke_b, alpha = style.Color(
                xocolor.get_stroke_color(), 1.0).get_rgba()
            fill_r, fill_g, fill_b, alpha = style.Color(
                xocolor.get_fill_color(), 1.0).get_rgba()

        if self.vertical:
            cairoutils.draw_round_rect(ctx, -1, -1, SIZE + 2, SIZE * 2 + 2, r)

            ctx.set_source_rgb(stroke_r, stroke_g, stroke_b)
            ctx.fill()

            cairoutils.draw_round_rect(ctx, 0, 0, SIZE, SIZE * 2, r)
            if selected:
                ctx.set_source_rgb(1, 1, 204.0 / 255.0)
            else:
                ctx.set_source_rgb(fill_r, fill_g, fill_b)
            ctx.fill()

            ctx.move_to(SIZE, 0)
            ctx.rel_line_to((SIZE / 8), (SIZE / 8))
            ctx.rel_line_to(0, SIZE * 2)
            ctx.rel_line_to(-(SIZE / 8), -(SIZE / 8))
            ctx.rel_line_to(0, -SIZE * 2)
            ctx.close_path()
            ctx.fill_preserve()
            ctx.set_source_rgb(stroke_r, stroke_g, stroke_b)
            ctx.stroke()

            ctx.move_to(0, SIZE * 2)
            ctx.rel_line_to((SIZE / 8), (SIZE / 8))
            ctx.rel_line_to(SIZE, 0)
            ctx.rel_line_to(- (SIZE / 8), -(SIZE / 8))
            ctx.rel_line_to(-SIZE, 0)
            ctx.close_path()
            ctx.set_source_rgb(fill_r, fill_g, fill_b)
            ctx.fill_preserve()
            ctx.set_source_rgb(stroke_r, stroke_g, stroke_b)
            ctx.stroke()

            if not self.reversed:
                self._draw_label_a(ctx, 0, 0)
                self._draw_label_b(ctx, 0, SIZE)
            else:
                self._draw_label_b(ctx, 0, 0)
                self._draw_label_a(ctx, 0, SIZE)

        else:
            cairoutils.draw_round_rect(ctx, -1, -1, SIZE * 2 + 2, SIZE + 2, r)
            ctx.set_source_rgb(stroke_r, stroke_g, stroke_b)
            ctx.fill()

            cairoutils.draw_round_rect(ctx, 0, 0, SIZE * 2, SIZE, r)
            if selected:
                ctx.set_source_rgb(1, 1, 204.0 / 255.0)
            else:
                ctx.set_source_rgb(fill_r, fill_g, fill_b)
            ctx.fill()

            ctx.move_to(SIZE * 2, 0)
            ctx.rel_line_to((SIZE / 8), (SIZE / 8))
            ctx.rel_line_to(0, SIZE)
            ctx.rel_line_to(-(SIZE / 8), -(SIZE / 8))
            ctx.rel_line_to(0, -SIZE)
            ctx.close_path()
            ctx.fill_preserve()
            ctx.set_source_rgb(stroke_r, stroke_g, stroke_b)
            ctx.stroke()

            ctx.move_to(0, SIZE)
            ctx.rel_line_to((SIZE / 8), (SIZE / 8))
            ctx.rel_line_to(SIZE * 2, 0)
            ctx.rel_line_to(-(SIZE / 8), -(SIZE / 8))
            ctx.rel_line_to(-SIZE * 2, 0)
            ctx.close_path()
            ctx.set_source_rgb(fill_r, fill_g, fill_b)
            ctx.fill_preserve()
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
