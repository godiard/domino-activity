#!/usr/bin/env python

# Domino con cuentas
# By Gonzalo Odiard, 2006 godiard at gmail.com
# GPL License - http://www.gnu.org/copyleft/gpl.html

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import GObject
from gi.repository import Gst

import cairo
import sys
import os

import json
import logging
from operator import attrgetter

from gettext import gettext as _
from sugar3.activity import activity
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics import style
from sugar3 import profile

from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton

from dominogame import DominoGame
from dominogame import DominoGamePoints
from dominopieceprocessor import PieceProcessorMathSimple
from dominopieceprocessor import PieceProcessorProductTable
from dominopieceprocessor import PieceProcessorPoints
from dominopieceprocessor import PieceProcessorFractions
from palettebox import PaletteBox

GObject.threads_init()
Gst.init(None)


class Domino(activity.Activity):

    """
    La activity arma la Toolbar, el canvas e inicia el juego
    """

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        toolbar_box = ToolbarBox()
        self.set_toolbar_box(toolbar_box)
        self.max_participants = 1
        self._activity_toolbar_button = ActivityToolbarButton(self)

        toolbar_box.toolbar.insert(self._activity_toolbar_button, 0)
        self._activity_toolbar_button.show()

        # lista con los puntajes
        self.list_points = []

        # lista de los processors
        self._processors = {}
        names = []

        proc = PieceProcessorMathSimple()
        self._processors[proc.get_name()] = proc
        names.append([proc.get_name(), proc.get_icon()])
        for number in range(2, 10):
            proc = PieceProcessorProductTable(number)
            self._processors[proc.get_name()] = proc
            names.append([proc.get_name(), proc.get_icon()])
        proc = PieceProcessorPoints()
        self._processors[proc.get_name()] = proc
        names.append([proc.get_name(), proc.get_icon()])
        proc = PieceProcessorFractions()
        self._processors[proc.get_name()] = proc
        names.append([proc.get_name(), proc.get_icon()])

        for name in names:
            # initialize points
            if self.get_points_by_name(name[0]) is None:
                game_points = DominoGamePoints()
                game_points.name = name[0]
                self.list_points.append(game_points)

        self._type_game_box = PaletteBox(names[0], names)

        toolbar_box.toolbar.insert(self._type_game_box, -1)

        self.btnStart = ToolButton('domino-new')
        self.btnStart.connect('clicked', self._start_game)
        self.btnStart.set_tooltip(_('Start'))
        toolbar_box.toolbar.insert(self.btnStart, -1)

        toolbar_box.toolbar.insert(Gtk.SeparatorToolItem(), -1)

        self.btnNew = ToolButton('list-add')
        self.btnNew.connect('clicked', self._add_piece)
        self.btnNew.set_tooltip(_('Get piece'))
        toolbar_box.toolbar.insert(self.btnNew, -1)

        self.btnPass = ToolButton('media-seek-forward')
        self.btnPass.connect('clicked', self._pass_next_player)
        self.btnPass.set_tooltip(_('Pass'))
        toolbar_box.toolbar.insert(self.btnPass, -1)

        self.btnScores = ToolButton('scores')
        self.btnScores.connect('clicked', self._show_scores)
        self.btnScores.set_tooltip(_('Scores'))
        toolbar_box.toolbar.insert(self.btnScores, -1)

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_size_request(0, -1)
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)

        toolbar_box.toolbar.insert(StopButton(self), -1)

        toolbar_box.show_all()

        self.drawingarea = Gtk.DrawingArea()
        self.drawingarea.show()
        self.drawingarea.set_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                                    Gdk.EventMask.EXPOSURE_MASK |
                                    Gdk.EventMask.TOUCH_MASK)

        self.drawingarea.connect('draw', self.__draw_cb)
        self.drawingarea.connect('event', self.__event_cb)

        self.connect('key-press-event', self.on_keypress)
        self.set_canvas(self.drawingarea)

        self.game = None
        self.surface = None
        self._pattern_surf = None
        self._start_game(None)
        self.drawingarea.queue_draw()
        self.pipeline = None
        self._last_game_type = None

        # Handle screen rotation
        Gdk.Screen.get_default().connect('size-changed', self.__configure_cb)

    def __configure_cb(self, event):
        if self.game:
            self.game.table.configure()
            self.drawingarea.set_size_request(
                self.game.table.screen_width, self.game.table.screen_height)
            self._pattern_surf = None
        self._start_game(None)

    def _create_backgroud_pattern(self):
        # read the image to paint the background
        if self.game.table.horizontal:
            background_file = "images/Wood.jpg"
        else:
            background_file = "images/Wood2.jpg"
        wood_pxb = GdkPixbuf.Pixbuf.new_from_file(background_file)

        # paint it over the pattern surface
        self._pattern_surf = cairo.ImageSurface(
            cairo.FORMAT_ARGB32,
            wood_pxb.get_width(), wood_pxb.get_height())
        pattern_ctx = cairo.Context(self._pattern_surf)

        pattern_ctx.rectangle(0, 0, wood_pxb.get_width(),
                              wood_pxb.get_height())
        Gdk.cairo_set_source_pixbuf(pattern_ctx, wood_pxb, 0, 0)
        pattern_ctx.fill()
        self._pattern_surf.flush()

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
        ctx.set_source_surface(self.surface)
        ctx.paint()

        if self.game.is_finished():
            win = (self.game.winner == self.game.ui_player)
            self.game.table.msg_end_game(ctx, win)
        else:
            player = self.game.ui_player
            # Dibujo la pieza seleccionada
            player.get_pieces()[player.order_piece_selected].draw(ctx, True)

    def _finish_game(self, win):
        self.add_points_by_name(self.game.processor.get_name(), win)
        self.btnNew.props.sensitive = False
        self.btnPass.props.sensitive = False
        self._last_game_type = self.game.processor.get_name()

    def __event_cb(self, widget, event):
        if self.game.is_finished():
            return

        if event.type in (Gdk.EventType.TOUCH_BEGIN,
                          Gdk.EventType.BUTTON_PRESS):
            x = int(event.get_coords()[1])
            y = int(event.get_coords()[2])

            if self.game.game_state == DominoGame.GAME_STATE_SELECT_PIECE:
                player = self.game.ui_player
                i = 0
                for piece in player.get_pieces():
                    if piece.visible and piece.check_touched(x, y):
                        player.order_piece_selected = i

                        if player.place_piece(piece):
                            player.end_play()
                    i += 1

    def draw_pieces(self):
        self.surface = cairo.ImageSurface(
            cairo.FORMAT_ARGB32, self.game.table.screen_width,
            self.game.table.screen_height)
        surf_ctx = cairo.Context(self.surface)

        # paint the background
        if self._pattern_surf is None:
            self._create_backgroud_pattern()
        back_pattern = cairo.SurfacePattern(self._pattern_surf)
        back_pattern.set_extend(cairo.EXTEND_REPEAT)
        surf_ctx.rectangle(0, 0, self.game.table.screen_width,
                           self.game.table.screen_height)
        surf_ctx.set_source(back_pattern)
        surf_ctx.fill()

        # sort from top left, to bottom right to not overdraw visually
        for piece in sorted(self.game.placed_pieces, key=attrgetter('x', 'y')):
            if piece.visible:
                piece.draw(surf_ctx, False)

        for player in self.game.players:
            self.game.table.arrange_pieces_player(player)
            pieces = player.get_pieces()
            # the first player have the pieces flipped
            flipped = player == self.game.players[0]
            # TODO: replace for m (m is needed below)
            for m in range(0, len(pieces)):
                piece = pieces[m]
                if piece.visible:
                    if self.game.game_state != \
                            DominoGame.GAME_STATE_LOCATE_PIECE \
                            or (m != self.game.ui_player.order_piece_selected):
                        piece.draw(surf_ctx, False, flipped)

        # if the automatic player passed, show  message
        if self.game.player_automatic_passed():
            self.game.table.msg_player_pass(surf_ctx)

        # to debug
        # self.game.table.show_values(surf_ctx, self.game.values)
        # self.game.table.mark_tile(surf_ctx, self.game.start)
        # self.game.table.mark_tile(surf_ctx, self.game.end)

    def _start_game(self, button):
        # Aqui comienza el juego
        processor = self._processors[self._type_game_box.get_value()[0]]

        self.game = DominoGame(processor)
        self.game.connect('piece-placed', self.__piece_placed_cb)
        self.game.connect('player-ended', self.__player_ended_cb)

        # Al principio se puede pedir pero no pasar
        self.btnNew.props.sensitive = True
        self.btnPass.props.sensitive = False

        self.game.start_game(2)
        self.draw_pieces()
        self.drawingarea.queue_draw()

    def _add_piece(self, button):
        if self.game.request_one_piece(self.game.ui_player):
            self.draw_pieces()
        else:
            self.btnNew.props.sensitive = False
            self.btnPass.props.sensitive = True

    def _pass_next_player(self, button):
        self.game.ui_player.has_passed = True
        self.game.ui_player.end_play()

        self.drawingarea.queue_draw()

    def _show_scores(self, button):
        ScoresWindow(self.get_window(), self.list_points,
                     self._last_game_type, self.game.table.horizontal)

    def __piece_placed_cb(self, game):
        self.draw_pieces()
        self.drawingarea.queue_draw()
        GObject.idle_add(self.tick)

    def tick(self):
        if self.pipeline is None:
            self.pipeline = Gst.Pipeline()
            self.player = Gst.ElementFactory.make('playbin', None)
            self.pipeline.add(self.player)
            sound_path = os.path.join(activity.get_bundle_path(), 'sounds',
                                      'tick.wav')
            self.player.set_property('uri', 'file://%s' % sound_path)
            self.bus = self.pipeline.get_bus()
            self.bus.add_signal_watch()

            self.bus.connect('message::eos', self.__on_eos_message)

        self.pipeline.set_state(Gst.State.PLAYING)

    def __on_eos_message(self, bus, msg):
        self.pipeline.set_state(Gst.State.NULL)

    def __player_ended_cb(self, game):
        self.draw_pieces()
        self.drawingarea.queue_draw()

        if len(self.game.pieces) > 0:
            # si hay piezas puede pedir pero no pasar
            self.btnNew.props.sensitive = True
            self.btnPass.props.sensitive = False
        else:
            # si no hay piezas no puede pedir pero si pasar
            self.btnNew.props.sensitive = False
            self.btnPass.props.sensitive = True

        if not self.game.player_automatic_playing():
            self.btnNew.props.sensitive = False
            self.btnPass.props.sensitive = False

        if not self.game.is_finished():
            if self.game.ENABLE_AUTO_MODE:
                GObject.timeout_add(300, game.start_next_player)
            else:
                GObject.timeout_add_seconds(2, game.start_next_player)
        else:
            win = (self.game.winner == self.game.ui_player)
            self._finish_game(win)

    def on_keypress(self, widget, event):
        if self._activity_toolbar_button.page.title.has_focus():
            return False

        if self.game.is_finished():
            return False

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

    def write_file(self, file_name):
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

    def read_file(self, file_name):
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


class ScoresWindow(Gtk.Window):

    def __init__(self, parent_xid, score_list, last_game_played, horizontal):
        Gtk.Window.__init__(self)
        self._parent_window_xid = parent_xid

        self._score_list = score_list
        self._last_game_played = last_game_played

        self.set_border_width(style.LINE_WIDTH)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_decorated(False)
        self.set_resizable(False)
        self.connect('realize', self.__realize_cb)
        # Handle screen rotation
        Gdk.Screen.get_default().connect('size-changed', self.__size_change_cb)
        self._init(horizontal)

    def _init(self, horizontal):
        vbox = Gtk.VBox()
        toolbar = BasicToolbar(_('Scoreboard'))
        toolbar.stop.connect('clicked', self.__stop_clicked_cb)
        vbox.pack_start(toolbar, False, False, 0)

        if horizontal:
            text_font_size = style.FONT_SIZE * 2
            hmargin = style.GRID_CELL_SIZE / 2
        else:
            text_font_size = style.FONT_SIZE * 1.5
            hmargin = style.GRID_CELL_SIZE / 3

        scores_grid = Gtk.Grid()
        scores_grid.set_column_spacing(style.DEFAULT_PADDING * 3)
        scores_grid.set_row_spacing(style.DEFAULT_PADDING)
        scores_grid.set_border_width(style.DEFAULT_SPACING)
        row = 0

        name = Gtk.Label()
        name.set_markup('<span font="%d" color="white">%s</span>' %
                        (text_font_size, _('Games')))
        name.set_halign(Gtk.Align.START)
        name.props.margin_bottom = style.DEFAULT_PADDING * 3
        scores_grid.attach(name, 0, row, 1, 1)

        played = Gtk.Label()
        played.set_markup('<span font="%d" color="white">%s</span>' %
                          (text_font_size, _('Played')))
        played.set_halign(Gtk.Align.CENTER)
        played.props.margin_left = hmargin
        played.props.margin_right = hmargin
        played.props.margin_bottom = style.DEFAULT_PADDING * 3

        scores_grid.attach(played, 1, row, 1, 1)

        win = Gtk.Label()
        win.set_markup('<span font="%d" color="white">%s</span>' %
                       (text_font_size, _('Won')))
        win.set_halign(Gtk.Align.CENTER)
        win.props.margin_left = hmargin
        win.props.margin_right = hmargin
        win.props.margin_bottom = style.DEFAULT_PADDING * 3
        scores_grid.attach(win, 2, row, 1, 1)

        lost = Gtk.Label()
        lost.set_markup('<span font="%d" color="white">%s</span>' %
                        (text_font_size, _('Lost')))
        lost.set_halign(Gtk.Align.CENTER)
        lost.props.margin_left = hmargin
        lost.props.margin_right = hmargin
        lost.props.margin_bottom = style.DEFAULT_PADDING * 3
        scores_grid.attach(lost, 3, row, 1, 1)

        row += 1

        for game_points in self._score_list:
            if game_points.name == self._last_game_played:
                color = profile.get_color().get_stroke_color()
            else:
                color = 'white'
            name = Gtk.Label()
            name.set_markup('<span font="%d" color="%s">%s</span>' %
                            (text_font_size, color, game_points.name))
            name.set_halign(Gtk.Align.START)
            scores_grid.attach(name, 0, row, 1, 1)

            played = Gtk.Label()
            played.set_markup('<span font="%d" color="%s">%s</span>' %
                              (text_font_size, color, str(game_points.played)))
            played.set_halign(Gtk.Align.END)
            scores_grid.attach(played, 1, row, 1, 1)

            win = Gtk.Label()
            win.set_markup('<span font="%d" color="%s">%s</span>' %
                           (text_font_size, color, str(game_points.win)))
            win.set_halign(Gtk.Align.END)
            scores_grid.attach(win, 2, row, 1, 1)

            lost = Gtk.Label()
            lost.set_markup('<span font="%d" color="%s">%s</span>' %
                            (text_font_size, color, str(game_points.lost)))
            lost.set_halign(Gtk.Align.END)
            scores_grid.attach(lost, 3, row, 1, 1)

            row += 1

        vbox.pack_start(scores_grid, False, False, 0)

        self.add(vbox)

        self.modify_bg(Gtk.StateType.NORMAL,
                       style.COLOR_TOOLBAR_GREY.get_gdk_color())

        self.show_all()

    def __size_change_cb(self, event):
        horizontal = Gdk.Screen.width() > Gdk.Screen.height()
        self.remove(self.get_children()[0])
        self._init(horizontal)

    def __stop_clicked_cb(self, button):
        self.destroy()

    def __realize_cb(self, widget):
        self.get_window().set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.get_window().set_decorations(Gdk.WMDecoration.BORDER)
        self.get_window().set_transient_for(self._parent_window_xid)


class BasicToolbar(Gtk.Toolbar):

    def __init__(self, title):
        GObject.GObject.__init__(self)
        self.modify_bg(Gtk.StateType.NORMAL,
                       style.COLOR_BLACK.get_gdk_color())

        label = Gtk.Label()
        label.set_markup('<b>%s</b>' % title)
        label.set_halign(Gtk.Align.START)
        tool_item = Gtk.ToolItem()
        tool_item.set_expand(True)
        tool_item.add(label)
        tool_item.show_all()
        tool_item.props.margin_left = style.GRID_CELL_SIZE / 2
        self.insert(tool_item, -1)

        self.separator = Gtk.SeparatorToolItem()
        self.separator.props.draw = False
        self.separator.set_expand(True)
        self.insert(self.separator, -1)

        self.stop = ToolButton(icon_name='dialog-cancel')
        self.stop.set_tooltip(_('Cancel'))
        self.insert(self.stop, -1)
        self.stop.show()
