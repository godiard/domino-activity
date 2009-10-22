import gobject
import gtk
import math, random

import pygtk
pygtk.require('2.0')
import getopt

import logging
from gettext import gettext as _
import sugar
from sugar.activity import activity
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.xocolor import XoColor

import dominoview
from  dominoview import Tile
from  dominopiece import DominoPiece


class DominoPlayer:

	"""
	Jugadores (automaticos o humanos) del domino
	"""

	def __init__(self,game,number):
		self.number = number
		self.name = _('Player ')+str(self.number)
		self.game = game
		self._pieces = []
		self.order_piece_selected = 0
		self.playing = False
		self.color = None
		# se usa para saber si este usuario paso la ultima vuelta
		self.has_passed = False 

	def set_pieces(self,pieces):
		self._pieces = pieces
		for n in range(0,len(self._pieces)):
			piece = self._pieces[n]
			piece.player = self
			piece.state = DominoPiece.PIECE_PLAYER
		self.order_piece_selected = 0
		
	def get_pieces(self):
		return self._pieces

	def play(self):
		#print "Play player",self.number
		self.playing = True
		#print "Cant piezas",len(self._pieces)
		if (self == self.game.ui_player):
			#print "Abilitando botones"
			self.game.game_state = self.game.GAME_STATE_SELECT_PIECE
			if (len(self.game.pieces) > 0):
				# si hay piezas puede pedir pero no pasar  
				self.game.btnNew.props.sensitive = True
				self.game.btnPass.props.sensitive = False
			else:
				# si no hay piezas no puede pedir pero si pasar
				self.game.btnNew.props.sensitive = False
				self.game.btnPass.props.sensitive = True


	def end_play(self):
		if (self == self.game.ui_player):			
			#print "Deshabilitando botones"
			self.game.btnPass.props.sensitive = False
			self.game.btnNew.props.sensitive = False
		#print "End player",self.number
		self.playing = False
		self.game.next_player(self.number).play()


	def remove_piece(self,piece):
		cantPieces = len(self._pieces)
		for n in range(0,len(self._pieces)):
			p = self._pieces[n]
			if (piece == p):
				self._pieces[n] = cantPieces
				self._pieces.remove(cantPieces)
				return

	def get_status(self):
		if (len(self._pieces) > 0):
			return self.name+' - '+str(len(self._pieces))+' '+_('pieces')+'.    '
		else:
			return self.name+' -  '+_('WIN')+'!!!!.    '


class SimpleAutoPlayer(DominoPlayer):

	"""
	Jugador automatico simple
	Busca la primera ficha que pueda ubicarse en alguna de las posiciones
	si no encuentra una pide
	NO TIENE NINGUNA ESTRATEGIA

	"""
	
	def play(self):
		#print "Jugando automatico"		
		if self.game.start == None:
			# si no hay ninguna pieza en el tablero ponemos la primera		
			piece = self._pieces[0]
			n,p = self.game.cantX / 2 - 1,self.game.cantY / 2 
			self._put_piece(piece,n,p)

			# seteamos comienzo y fin del domino
			startTile = Tile(n,p)
			startTile.value = piece.a
			startTile.piece = piece
			self.game.start = startTile

			endTile = Tile(n + 1,p)
			endTile.value = piece.b
			endTile.piece = piece
			self.game.end = endTile
			
		else:
			#print "automatica siguiente"
			# buscamos si tenemos alguna ficha que corresponda
			# en el comienzo
			ok = False
			piece = self._get_piece_with_value(self.game.start.value)
			if (piece != None):
				n,p,piece,ok = self._test_good_position(self.game.start,piece)
				if (ok):
					self._put_piece(piece,n,p)
			if (not ok):
				# en el fin
				piece = self._get_piece_with_value(self.game.end.value)
				if (piece != None):
					n,p,piece,ok = self._test_good_position(self.game.end,piece)
					if (ok):
						self._put_piece(piece,n,p)
			if (not ok):
				# pido una hasta que sea valida o no hayan mas disponibles
				# si no encontramos pedimos hasta que alguna sirva
				while (not ok):
					#print "Pido pieza"
					pieces = self.game.take_pieces(1)
					if (len(pieces) > 0): 
						piece = pieces[0]
						piece.player = self
						self.get_pieces().append(piece)
						n,p,piece,ok = self._test_good_position(self.game.start,piece)
						if (ok):
							self._put_piece(piece,n,p)
						if (not ok):
							# en el fin
							n,p,piece,ok = self._test_good_position(self.game.end,piece)
							if (ok):
								self._put_piece(piece,n,p)
					else:
						ok = True # No hay mas piezas
						self.has_passed = True
			if (not ok):
				self.has_passed = True					

		# juega el siguiente jugador
		self.end_play()

	def _put_piece(self,piece,n,p):
		self.piece_selected = None
		x,y = self.game.table.get_tile_position(n,p)
		self.game.put_piece(self,piece,n,p)


	# elige una pieza que tenga un valor
	def _get_piece_with_value(self,value):
		for n in range(0,len(self._pieces)):
			piece = self._pieces[n]
			if (piece.player == self):
				#print "get_piece_with_value",piece.a, piece.b
				if (piece.a == value) or (piece.b == value):
					return piece
		return None
	


	
	def _test_good_position(self,tile,piece):
		n,p = tile.n,tile.p
		# Pruebo con las cuatro posiciones que rodean a n,p
		# con la pieza en cuatro posiciones
		for i in range(0,3):
			# Combino las cuatro posiciones posibles
			if (i == 0):
				piece.vertical = False
				piece.reversed = False
			if (i == 1):
				piece.vertical = True
				piece.reversed = False
			if (i == 2):
				piece.vertical = False
				piece.reversed = True
			if (i == 3):
				piece.vertical = True
				piece.reversed = True
			if (self.game.test_good_position(piece,n+1,p)):	
				return n+1,p,piece,True
			if (self.game.test_good_position(piece,n,p+1)):	
				return n,p+1,piece,True
			if (self.game.test_good_position(piece,n-1,p)):	
				return n-1,p,piece,True
			if (self.game.test_good_position(piece,n,p-1)):	
				return n,p-1,piece,True
		# Si no encuentro ninguna posicion valida devuelvo None en la piece
		return n,p,piece,False

