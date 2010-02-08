#!/usr/bin/env python

### Domino con cuentas
### By Gonzalo Odiard, 2006 godiard at gmail.com
### GPL License - http://www.gnu.org/copyleft/gpl.html

# Tutorial  de cairo interesante
# http://tortall.net/mu/wiki/CairoTutorial

# http://www.redhatmagazine.com/2007/04/05/building-the-xo-porting-a-pygtk-game-to-sugar-part-one/

# Style guide : http://www.python.org/dev/peps/pep-0008/

import gobject
import gtk
import cairo
import pango
import math, random
import os,sys

import simplejson

import pygtk
pygtk.require('2.0')
import getopt

import logging
from gettext import gettext as _
import sugar
from sugar.activity import activity
from sugar.graphics.toolbutton import ToolButton

import dominoview
from dominoview import DominoTableView
from dominogame import DominoGame
from dominogame import DominoGamePoints
from dominopiece import DominoPiece
import dominopieceprocessor
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
    
        # Creo la toolbar y agrego los botones

        toolbox = activity.ActivityToolbox(self)
        self.toolbar = gtk.Toolbar()

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
        cmbItem = gtk.ToolItem()
        self.cmbTipoPiezas = gtk.combo_box_new_text()

        self.read_file()

        for n in range(0,len(self.list_processors)):
            self.cmbTipoPiezas.append_text(self.list_processors[n].get_name())
            # inicializo puntajes
            if (self.get_points_by_name(self.list_processors[n].get_name()) == None):
                game_points = DominoGamePoints()
                game_points.name = self.list_processors[n].get_name()
                self.list_points.append(game_points)


        cmbItem.add(self.cmbTipoPiezas)
        self.toolbar.insert(cmbItem, -1)
        self.cmbTipoPiezas.show()
        cmbItem.show()
        self.cmbTipoPiezas.set_active(0)

        self.btnStart = ToolButton('dialog-ok')
        self.btnStart.connect('clicked', self._start_game)
        self.btnStart.set_tooltip(_('Start'))
        self.toolbar.insert(self.btnStart, -1)
        self.btnStart.show()

        self.btnNew = ToolButton('list-add')
        self.btnNew.connect('clicked', self._add_piece)
        self.btnNew.set_tooltip(_('Get piece'))
        self.toolbar.insert(self.btnNew, -1)
        self.btnNew.show()

        self.btnPass = ToolButton('go-next')
        self.btnPass.connect('clicked', self._pass_next_player)
        self.btnPass.set_tooltip(_('Pass'))
        self.toolbar.insert(self.btnPass, -1)
        self.btnPass.show()

        self.btnScores = ToolButton('scores')
        self.btnScores.connect('clicked', self._show_scores)
        self.btnScores.set_tooltip(_('Scores'))
        self.toolbar.insert(self.btnScores, -1)
        self.btnScores.show()
        

        toolbox.add_toolbar(_('Domino'), self.toolbar)
        self.toolbar.show()
        self.set_toolbox(toolbox)
        toolbox.show()

        toolbox.set_current_toolbar(1)

        # Creo el Canvas y el CanvasBox donde dibujaremos todo el tablero y las fichas
        self.drawingarea = gtk.DrawingArea()
        self.drawingarea.set_size_request(dominoview.SCREEN_WIDTH,dominoview.SCREEN_HEIGHT)
        self.drawingarea.show()
        self.drawingarea.connect('expose-event', self.on_drawing_area_exposed)
        self.connect('key-press-event',self.on_keypress)
        self.set_canvas(self.drawingarea)

        self.game = None
        self.show_scores = False 

        self.surface = None

        self.drawingarea.queue_draw()


    def get_points_by_name(self,game_processor_name):
        for n in range(0,len(self.list_points)):
            if (self.list_points[n].name == game_processor_name):
                return self.list_points[n]
        return None

    def add_points_by_name(self,game_processor_name,win):
        for n in range(0,len(self.list_points)):
            if (self.list_points[n].name == game_processor_name):
                self.list_points[n].played = self.list_points[n].played + 1
                if (win) :                
                    self.list_points[n].win = self.list_points[n].win +1
                else :
                    self.list_points[n].lost = self.list_points[n].lost +1


    def on_drawing_area_exposed(self,drawingarea, event):
        x, y, width, height = drawingarea.allocation
        self.ctx = drawingarea.window.cairo_create()


        if (self.show_scores): 
            table = DominoTableView()
            table.show_scores(self.ctx,self.list_points)
            return

        if (self.game == None):
            table = DominoTableView()
            table.help(self.ctx)
            return

        self.ctx.set_source_surface(self.surface)
        self.ctx.paint()


        # test end game (se puede poner en otro metodo)
        end_game = False
        win = False

        # Dibujo la pieza seleccionada
        player = self.game.ui_player
        player.get_pieces()[player.order_piece_selected].draw(self.ctx,True)

        for n in range(0,len(self.game.players)):
            # dibujo las piezas del jugador
            player = self.game.players[n]
            pieces = player.get_pieces()
            if (len(pieces) == 0):
                end_game = True
                if (self.game.ui_player == player):
                    win = True

        # Chequeo si todos los jugadores pasaron

        all_has_passed = True
        for n in range(0,len(self.game.players)):
            player = self.game.players[n]
            if (not player.has_passed):
                all_has_passed = False 

        # si todos pasaron veo quien tiene menos fichas
        if (all_has_passed):
            min_cant_pieces = 100
            player_with_minus_pieces = None
            for n in range(0,len(self.game.players)):
                player = self.game.players[n]
                if (len(player.get_pieces()) < min_cant_pieces):
                    min_cant_pieces = len(player.get_pieces())
                    player_with_minus_pieces = player

            end_game = True        
                    
            # no estoy manejando un empate... (ambos jugadores con la misma cantidad de piezas)

            if (player_with_minus_pieces == player):
                win = True

        if (self.game.table):
            self.game.table.show_status(self.ctx,self.game.get_status())

        if (end_game):
            self.add_points_by_name(self.game.processor.get_name(),win)
            self.game.table.msg_end_game(self.ctx,win)            


    def draw_pieces(self):
        sys.stdout.write("DIBUJANDO \n")
        sys.stdout.flush()
        self.surface=cairo.ImageSurface(cairo.FORMAT_ARGB32,dominoview.SCREEN_WIDTH,dominoview.SCREEN_HEIGHT)
        surf_ctx=cairo.Context(self.surface)

        if (self.game.table):
            self.game.table.paint(surf_ctx)

        # ordeno la lista de las fichas puestas desde arriba a la izq hacia abajo a la derecha
        # para que se encimen bien cuando se dibujan    
        self.game.placed_pieces.sort(lambda pieceA, pieceB: pieceA.x - pieceB.x + pieceA.y * 100 - pieceB.y * 100)

        for n in range(0,len(self.game.placed_pieces)):
            piece = self.game.placed_pieces[n]
            if (piece.visible):
                piece.draw(surf_ctx,False)

        #for n in range(0,len(self.game.players)):
        # dibujo las piezas del jugador
        player = self.game.ui_player
        pieces = player.get_pieces()
        for m in range(0,len(pieces)):
            piece = pieces[m]
            if (piece.visible):
                if (self.game.game_state != DominoGame.GAME_STATE_LOCATE_PIECE) or (m != self.game.ui_player.order_piece_selected):
                    piece.draw(surf_ctx,False)

    def _start_game(self,button):

        if (self.show_scores):
            self.show_scores = False 

        # Aqui comienza el juego    
        processor = self.list_processors[self.cmbTipoPiezas.get_active()]

        self.game = DominoGame(processor,self.drawingarea)

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

    def _show_scores(self,button):
        self.show_scores = True
        self.drawingarea.queue_draw()


    def on_keypress(self, widget, event):
        key = gtk.gdk.keyval_name(event.keyval)

        # Agrego las teclas de juego de la XO (Circulo arriba = KP_Page_Up , X  = KP_Page_Down, Check = KP_End

        if key in ('KP_Up','KP_Right','KP_Down','KP_Left','KP_Page_Up','KP_Page_Down','KP_End', 'space','KP_8','KP_6','KP_2','KP_4','Escape','Return','Up','Down','Left','Right'):
            if (key in ('KP_Page_Up')):
                key = 'space'
            if (key in ('KP_Page_Down')):
                key = 'Escape'
            if (key in ('KP_End')):
                key = 'Return'

            if (key in ('Up', 'KP_8')):
                key = 'KP_Up'
            if (key in ('Right', 'KP_6')):
                key = 'KP_Rigth'
            if (key in ('Down', 'KP_2')):
                key = 'KP_Down'
            if (key in ('Left', 'KP_4')):
                key = 'KP_Left'
            self.key_action(key)
        # Para saber que codigo viene
        #else:
        #    print gtk.gdk.keyval_name(event.keyval)
        #    sys.stdout.write("keyval "+str(event.keyval)+" key "+key+"\n")
        #    sys.stdout.flush()
        return True

    def key_action(self, key):
        redraw = False
        if (self.show_scores):
            self.show_scores = False 
            redraw = True

        if (self.game.game_state == DominoGame.GAME_STATE_SELECT_PIECE):
            # Seleccionamos las distintas piezas
            if ((key == 'KP_Up') or (key == 'KP_Right')):
                if (self.game.ui_player.order_piece_selected    < len(self.game.ui_player.get_pieces()) - 1) :
                    self.game.ui_player.order_piece_selected = self.game.ui_player.order_piece_selected +1
                else:
                    self.game.ui_player.order_piece_selected = 0
                redraw = True
            if ((key == 'KP_Down') or (key == 'KP_Left')):                    
                if (self.game.ui_player.order_piece_selected    > 0) :
                    self.game.ui_player.order_piece_selected = self.game.ui_player.order_piece_selected - 1
                else:
                    self.game.ui_player.order_piece_selected = len(self.game.ui_player.get_pieces()) - 1
                redraw = True

            if ((key == 'Return')):            
                # Elegimos una pieza para jugar
                self.game.game_state = DominoGame.GAME_STATE_LOCATE_PIECE
                piece = self.game.ui_player.get_pieces()[self.game.ui_player.order_piece_selected]
                piece.rotate()
                nIni = int(self.game.table.cantX / 2)
                pIni = self.game.table.cantY - 2
                piece.x,piece.y = self.game.table.get_tile_position(nIni,pIni)
                self.draw_pieces()
                redraw = True

        elif (self.game.game_state == DominoGame.GAME_STATE_LOCATE_PIECE):
            # Movemos la pieza por el tablero
            # con space la giramos y con escape la volvemos a la pila de fichas del jugador
            piece = self.game.ui_player.get_pieces()[self.game.ui_player.order_piece_selected]
            if ((key == 'KP_Up') or (key == 'KP_Right') or (key == 'KP_Down') or (key == 'KP_Left') or (key == 'Return')):
                n,p = self.game.table.get_tile_coord(piece.x,piece.y)
                n_ori , p_ori = n,p
            if (key == 'KP_Up') :
                if (p > 0):
                    p = p - 1

            if (key == 'KP_Down') :
                if (p < self.game.table.cantY):
                    p = p + 1

            if (key == 'KP_Left') :
                if (n > 0):
                    n = n - 1

            if (key == 'KP_Right') :
                if (n <  self.game.table.cantX):
                    n = n + 1

            if ((key == 'KP_Up') or (key == 'KP_Right') or (key == 'KP_Down') or (key == 'KP_Left')):
                if (self.game.test_in_board(piece,n,p)):
                    piece.x,piece.y = self.game.table.get_tile_position(n,p)
                    redraw = True

            if (key == 'Escape'):
                # volvemos al modo de seleccion de piezas
                self.game.game_state = DominoGame.GAME_STATE_SELECT_PIECE
                self.game.show_pieces_player(self.game.ui_player)
                self.draw_pieces()
                redraw = True

            if (key == 'space'):
                # giro la pieza
                piece.rotate()
                redraw = True

            if (key == 'Return'):
                # posiciona la pieza si es posible
                if (self.game.test_good_position(piece,n,p)):
                    self.game.put_piece(piece.player,piece,n,p)
                    self.game.show_pieces_player(piece.player)
                    piece.player.end_play()
                    self.draw_pieces()
                    redraw = True

    
        if (redraw) :
            self.drawingarea.queue_draw()
        return


    def can_close(self):
        #save the file itself
        #act_root = os.getenv("SUGAR_ACTIVITY_ROOT")
        act_root = self.get_activity_root()
        file_name = os.path.join(act_root, "data","Scores.json")
        print "write file name",file_name
        
        data_points = []
        for points in self.list_points:
            data = {}
            data["name"] = points.name            
            data["played"] = points.played            
            data["win"] = points.win            
            data["lost"] = points.lost            
            data_points.append(data)
            
        try:
            print "antes de abrir archivo"
            fd = open(file_name, 'wt')
            print "antes de json"
            simplejson.dump(data_points, fd)
            print "desppues de json"
            print "antes de cerrar"
            fd.close()
            print "despues de cerrar"
        except:
            print "Write error:", sys.exc_info()[0]        

        return True    



    def read_file(self):
        #act_root = os.getenv("SUGAR_ACTIVITY_ROOT")
        act_root = self.get_activity_root()
        file_name = os.path.join(act_root, "data","Scores.json")
        print file_name
        
        if os.path.exists(file_name):
            fd = open(file_name, 'rt')
            try:
                # lo meto en una variable intermedia por si hay problemas
                data_points = simplejson.load(fd)
                
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
                print "Error leyendo puntajes", sys.exc_info()[0] 
            finally:
                fd.close()
        
    # Reimplemento close con la correccion a http://bugs.sugarlabs.org/ticket/1714    
        
    def close(self, skip_save=False):
        """Request that the activity be stopped and saved to the Journal

        Activities should not override this method, but should implement
        write_file() to do any state saving instead. If the application wants
        to control wether it can close, it should override can_close().
        """
        if not self.can_close():
            return

        #if skip_save or self.metadata.get('title_set_by_user', '0') == '1':
        if skip_save or self._jobject is None or \
            self.metadata.get('title_set_by_user', '0') == '1': 
            if not self._closing:
                if not self._prepare_close(skip_save):
                    return

            if not self._updating_jobject:
                self._complete_close()
        else:
            title_alert = NamingAlert(self, get_bundle_path())
            title_alert.set_transient_for(self.get_toplevel())
            title_alert.show()
            self.reveal()



