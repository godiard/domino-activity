#!/usr/bin/env python

# Domino con cuentas
# By Gonzalo Odiard, 2006 godiard at gmail.com
# GPL License - http://www.gnu.org/copyleft/gpl.html

from gi.repository import Gtk
from gi.repository import Gdk
import cairo
import os
import sys

import json
import logging

from gettext import gettext as _
from sugar3.activity import activity
from sugar3.graphics.toolbutton import ToolButton

from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton

import dominoview
from dominoview import DominoTableView
from dominogame import DominoGame
from dominogame import DominoGamePoints
from dominopiece import DominoPiece
from dominopieceprocessor import PieceProcessorMathSimple
from dominopieceprocessor import PieceProcessorProductTable
from dominopieceprocessor import PieceProcessorPoints
from dominopieceprocessor import PieceProcessorFractions


class Domino(activity.Activity):

    """
    La activity arma la Toolbar, el canvas e inicia el juego
    """

    def __init__(self, handle):
        activity.Activity.__init__(self, handle, create_jobject=False)

        toolbar_box = ToolbarBox()
        self.set_toolbar_box(toolbar_box)

        self._activity_toolbar_button = ActivityToolbarButton(self)

        toolbar_box.toolbar.insert(self._activity_toolbar_button, 0)
        self._activity_toolbar_button.show()

        # lista con los puntajes
        self.list_points = []

        # lista de los processors
        self.list_processors = []

        self.list_processors.append(PieceProcessorMathSimple())
        self.list_processors.append(PieceProcessorProductTable(2))
        self.list_processors.append(PieceProcessorProductTable(3))
        self.list_processors.append(PieceProcessorProductTable(4))
        self.list_processors.append(PieceProcessorProductTable(5))
        self.list_processors.append(PieceProcessorProductTable(6))
        self.list_processors.append(PieceProcessorProductTable(7))
        self.list_processors.append(PieceProcessorProductTable(8))
        self.list_processors.append(PieceProcessorProductTable(9))
        self.list_processors.append(PieceProcessorPoints())
        self.list_processors.append(PieceProcessorFractions())

        # agrego combo para tipo de juego
        cmbItem = Gtk.ToolItem()
        self.cmbTipoPiezas = Gtk.ComboBoxText()

        self.read_file()

        for processor in self.list_processors:
            # inicializo puntajes
            name = processor.get_name()
            self.cmbTipoPiezas.append_text(name)
            if self.get_points_by_name(name) is None:
                game_points = DominoGamePoints()
                game_points.name = name
                self.list_points.append(game_points)

        cmbItem.add(self.cmbTipoPiezas)
        toolbar_box.toolbar.insert(cmbItem, -1)
        self.cmbTipoPiezas.show()
        cmbItem.show()
        self.cmbTipoPiezas.set_active(0)

        self.btnStart = ToolButton('dialog-ok')
        self.btnStart.connect('clicked', self._start_game)
        self.btnStart.set_tooltip(_('Start'))
        toolbar_box.toolbar.insert(self.btnStart, -1)
        self.btnStart.show()

        self.btnNew = ToolButton('list-add')
        self.btnNew.connect('clicked', self._add_piece)
        self.btnNew.set_tooltip(_('Get piece'))
        toolbar_box.toolbar.insert(self.btnNew, -1)
        self.btnNew.show()

        self.btnPass = ToolButton('go-next')
        self.btnPass.connect('clicked', self._pass_next_player)
        self.btnPass.set_tooltip(_('Pass'))
        toolbar_box.toolbar.insert(self.btnPass, -1)
        self.btnPass.show()

        self.btnScores = ToolButton('scores')
        self.btnScores.connect('clicked', self._show_scores)
        self.btnScores.set_tooltip(_('Scores'))
        toolbar_box.toolbar.insert(self.btnScores, -1)
        self.btnScores.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_size_request(0, -1)
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        toolbar_box.show_all()

        self.drawingarea = Gtk.DrawingArea()
        self.drawingarea.set_size_request(dominoview.SCREEN_WIDTH,
                                          dominoview.SCREEN_HEIGHT)
        self.drawingarea.show()
        self.drawingarea.set_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                                    Gdk.EventMask.EXPOSURE_MASK |
                                    Gdk.EventMask.TOUCH_MASK)

        self.drawingarea.connect('draw', self.__draw_cb)
        self.drawingarea.connect('event', self.__event_cb)

        self.connect('key-press-event', self.on_keypress)
        self.set_canvas(self.drawingarea)

        self.game = None
        self.show_scores = False
        self.surface = None
        self.drawingarea.queue_draw()

    def get_points_by_name(self, game_processor_name):
        for points in self.list_points:
            if points == game_processor_name:
                return points
        return None

    def add_points_by_name(self, game_processor_name, win):
        for points in self.list_points:
            if (points.name == game_processor_name):
                points.played = points.played + 1
                if win:
                    points.win = points.win + 1
                else:
                    points.lost = points.lost + 1

    def __draw_cb(self, drawingarea, ctx):

        if (self.show_scores):
            table = DominoTableView()
            table.show_scores(ctx, self.list_points)
            return

        if self.game is None:
            table = DominoTableView()
            table.help(ctx)
            return

        ctx.set_source_surface(self.surface)
        ctx.paint()

        # test end game (se puede poner en otro metodo)
        end_game = False
        win = False

        # Dibujo la pieza seleccionada
        player = self.game.ui_player
        player.get_pieces()[player.order_piece_selected].draw(ctx, True)

        for player in self.game.players:
            # dibujo las piezas del jugador
            pieces = player.get_pieces()
            if len(pieces) == 0:
                end_game = True
                if self.game.ui_player == player:
                    win = True

        # Chequeo si todos los jugadores pasaron

        all_has_passed = True
        for player in self.game.players:
            if (not player.has_passed):
                all_has_passed = False

        # si todos pasaron veo quien tiene menos fichas
        if all_has_passed:
            min_cant_pieces = 100
            player_with_minus_pieces = None
            for player in self.game.players:
                if len(player.get_pieces()) < min_cant_pieces:
                    min_cant_pieces = len(player.get_pieces())
                    player_with_minus_pieces = player

            end_game = True

            # no estoy manejando un empate
            # (ambos jugadores con la misma cantidad de piezas)

            if player_with_minus_pieces == player:
                win = True

        if self.game.table:
            self.game.table.show_status(ctx, self.game.get_status())

        if end_game:
            self.add_points_by_name(self.game.processor.get_name(), win)
            self.game.table.msg_end_game(ctx, win)

    def __event_cb(self, widget, event):
        if event.type in (Gdk.EventType.TOUCH_BEGIN,
                          Gdk.EventType.BUTTON_PRESS):
            x = int(event.get_coords()[1])
            y = int(event.get_coords()[2])

            if self.game.game_state == DominoGame.GAME_STATE_SELECT_PIECE:
                for player in self.game.players:
                    i = 0
                    for piece in player.get_pieces():
                        if piece.visible and piece.check_touched(x, y):
                            player.order_piece_selected = i
                            self.drawingarea.queue_draw()
                        i += 1

    def draw_pieces(self):
        self.surface = cairo.ImageSurface(
            cairo.FORMAT_ARGB32, dominoview.SCREEN_WIDTH,
            dominoview.SCREEN_HEIGHT)
        surf_ctx = cairo.Context(self.surface)

        if (self.game.table):
            self.game.table.paint(surf_ctx)

        # ordeno la lista de las fichas puestas desde arriba a la izq
        # hacia abajo a la derecha
        # para que se encimen bien cuando se dibujan
        self.game.placed_pieces.sort(
            lambda pieceA,
            pieceB: int(pieceA.x - pieceB.x + pieceA.y * 100 - pieceB.y * 100))

        for piece in self.game.placed_pieces:
            if piece.visible:
                piece.draw(surf_ctx, False)

        for player in self.game.players:
            pieces = player.get_pieces()
            # TODO: replace for m (m is needed below)
            for m in range(0, len(pieces)):
                piece = pieces[m]
                if piece.visible:
                    if self.game.game_state != \
                            DominoGame.GAME_STATE_LOCATE_PIECE \
                            or (m != self.game.ui_player.order_piece_selected):
                        piece.draw(surf_ctx, False)

        # to debug
        self.game.table.show_values(surf_ctx, self.game.values)
        self.game.table.mark_tile(surf_ctx, self.game.start)
        self.game.table.mark_tile(surf_ctx, self.game.end)

    def _start_game(self, button):
        if self.show_scores:
            self.show_scores = False

        # Aqui comienza el juego
        processor = self.list_processors[self.cmbTipoPiezas.get_active()]

        self.game = DominoGame(processor, self.drawingarea)

        self.game.btnPass = self.btnPass
        self.game.btnNew = self.btnNew
        # Al principio se puede pedir pero no pasar
        self.game.btnNew.props.sensitive = True
        self.game.btnPass.props.sensitive = False

        self.game.start_game(2)
        self.game.show_pieces_player(self.game.ui_player)
        self.draw_pieces()
        self.drawingarea.queue_draw()

    def _add_piece(self, button):
        pieces = self.game.take_pieces(1)
        if (len(pieces) > 0):
            piece = pieces[0]
            self.game.ui_player.get_pieces().append(piece)
            # esto no es mejor hay que hacerlo en la creacion?
            piece.player = self.game.ui_player
            piece.state = DominoPiece.PIECE_PLAYER
            self.game.show_pieces_player(self.game.ui_player)
            self.draw_pieces()
            self.drawingarea.queue_draw()
        else:
            self.game.btnNew.props.sensitive = False
            self.game.btnPass.props.sensitive = True

    def _pass_next_player(self, button):
        if (self.show_scores):
            self.show_scores = False
        else:
            self.game.ui_player.has_passed = True
            self.game.ui_player.end_play()

        self.drawingarea.queue_draw()

    def _show_scores(self, button):
        self.show_scores = True
        self.drawingarea.queue_draw()

    def on_keypress(self, widget, event):
        key = Gdk.keyval_name(event.keyval)
        # Agrego las teclas de juego de la XO (Circulo arriba = KP_Page_Up,
        # X  = KP_Page_Down, Check = KP_End

        if key in ('KP_Up', 'KP_Right', 'KP_Down', 'KP_Left', 'KP_Page_Up',
                   'KP_Page_Down', 'KP_End', 'space', 'KP_8', 'KP_6', 'KP_2',
                   'KP_4', 'Escape', 'Return', 'Up', 'Down', 'Left', 'Right'):
            if key == 'KP_Page_Up':
                key = 'space'
            elif key == 'KP_Page_Down':
                key = 'Escape'
            elif key == 'KP_End':
                key = 'Return'
            elif key in ('Up', 'KP_8'):
                key = 'KP_Up'
            elif key in ('Right', 'KP_6'):
                key = 'KP_Right'
            elif key in ('Down', 'KP_2'):
                key = 'KP_Down'
            elif key in ('Left', 'KP_4'):
                key = 'KP_Left'
            self.key_action(key)
        return True

    def key_action(self, key):
        redraw = False
        if self.show_scores:
            self.show_scores = False
            redraw = True

        if self.game.game_state == DominoGame.GAME_STATE_SELECT_PIECE:
            # Seleccionamos las distintas piezas
            if key == 'KP_Up' or key == 'KP_Right':
                if (self.game.ui_player.order_piece_selected <
                        len(self.game.ui_player.get_pieces()) - 1):
                    self.game.ui_player.order_piece_selected = \
                        self.game.ui_player.order_piece_selected + 1
                else:
                    self.game.ui_player.order_piece_selected = 0
                redraw = True
            if key == 'KP_Down' or key == 'KP_Left':
                if self.game.ui_player.order_piece_selected > 0:
                    self.game.ui_player.order_piece_selected = \
                        self.game.ui_player.order_piece_selected - 1
                else:
                    self.game.ui_player.order_piece_selected = \
                        len(self.game.ui_player.get_pieces()) - 1
                redraw = True

            if key == 'Return':
                # Elegimos una pieza para jugar
                player = self.game.ui_player
                piece = player.get_pieces()[player.order_piece_selected]

                if player.place_piece(piece):
                    player.end_play()
                    self.draw_pieces()

                redraw = True
        if redraw:
            self.drawingarea.queue_draw()
        return

    def can_close(self):
        # save the file itself
        act_root = self.get_activity_root()
        file_name = os.path.join(act_root, "data", "Scores.json")

        data_points = []
        for points in self.list_points:
            data = {}
            data["name"] = points.name
            data["played"] = points.played
            data["win"] = points.win
            data["lost"] = points.lost
            data_points.append(data)

        try:
            fd = open(file_name, 'wt')
            json.dump(data_points, fd)
            fd.close()
        except:
            logging.error("Write error: %s", sys.exc_info()[0])

        return True

    def read_file(self):
        act_root = self.get_activity_root()
        file_name = os.path.join(act_root, "data", "Scores.json")

        if os.path.exists(file_name):
            fd = open(file_name, 'rt')
            try:
                # lo meto en una variable intermedia por si hay problemas
                data_points = json.load(fd)

                self.list_points = []
                for data in data_points:
                    # inicializo puntajes
                    points = DominoGamePoints()
                    points.name = data["name"]
                    points.played = data["played"]
                    points.win = data["win"]
                    points.lost = data["lost"]
                    self.list_points.append(points)
            except:
                logging.error("Error leyendo puntajes %s", sys.exc_info()[0])
            finally:
                fd.close()
