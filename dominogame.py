import gobject
import gtk
import math, random

import pygtk
pygtk.require('2.0')
import getopt

import sys
from gettext import gettext as _

from sugar import profile

from dominopiece import DominoPiece
import dominoview
from dominoview import Tile
from dominoview import DominoTableView
import dominoplayer
from dominoplayer import DominoPlayer
from dominoplayer import SimpleAutoPlayer

from dominopieceprocessor import PieceProcessorMathSimple


class DominoGame:

	"""
	Esta es la clase principal del juego
	"""

	# estados del juego
	GAME_STATE_SELECT_PIECE = 1;
	GAME_STATE_LOCATE_PIECE = 2;
	GAME_STATE_ANOTHER_USER = 3;
	GAME_STATE_FINISH_GAME  = 4;

	def __init__(self,processor,drawingarea):
		self.ui_player = None
		self.table = DominoTableView()
		self.pieces = []
		self.placed_pieces = []
		self.game_state = DominoGame.GAME_STATE_SELECT_PIECE
		self.players = []
		self.values = []	
		self.cantX = self.table.cantX
		self.cantY = self.table.cantY
		for n in range(0,self.cantX):
			self.values.append([])
			for p in range(0,self.cantY):
				tile = Tile(n,p)
				self.values[n].append(tile)
		# primera y ultima posicion de las piezas
		self.start = None
		self.end = None
		
		self.processor = processor
		self.drawingarea = drawingarea

	def next_player(self,num_player):
		if (num_player >= len(self.players)-1):
			return self.players[0]
		else:
			return self.players[num_player+1]

	# Posiciona una pieza en el tablero
	def put_piece(self,player,piece,n,p):
		player.remove_piece(piece)

		valueA = piece.a
		valueB = piece.b
		if piece.reversed:
			valueA = piece.b
			valueB = piece.a

		self.values[n][p].value = valueA
		if piece.vertical:
			self.values[n][p+1].value = valueB
		else:
			self.values[n+1][p].value = valueB

		self.values[n][p].piece = piece
		if piece.vertical:
			self.values[n][p+1].piece = piece
		else:
			self.values[n+1][p].piece = piece

		piece.state = DominoPiece.PIECE_PLACED
		piece.visible = True
		piece.x,piece.y = self.table.get_tile_position(n,p)
		self.placed_pieces.append(piece)
		player.order_piece_selected = 0
		player.has_passed = False
		self.drawingarea.queue_draw()


	def test_in_board(self,dominoPiece,n,p):
		n1 = n
		p1 = p
		n2 = n
		p2 = p
		if (not dominoPiece.vertical):
			n2 = n2 + 1
		else:
			p2 = p2 + 1

		test = not ((n1 < 0) or (p1 < 1) or (n2 > self.cantX-1) or ( p2 > self.cantY))
		#sys.stdout.write("cantX "+str(self.cantX)+" cantY "+str(self.cantY)+"vert "+str(dominoPiece.vertical)+" rev "+str(dominoPiece.reversed)+" -- ")
		#sys.stdout.write(" n "+str(n)+" n1 "+str(n1)+" n2 "+str(n2)+" p "+str(p)+" p1 "+str(p1)+" p2 "+str(p2)+" = "+str(test)+"\n")
		#sys.stdout.flush()
		return test

	def test_good_position(self,dominoPiece,n,p):
		try:
			if (n < 0) or (p < 0) or (n > self.cantX) or ( p > self.cantY):
				#print "Fuera de los limites"
				return False
			if (dominoPiece.vertical):
				if ((p+1) > self.cantY): 
					#print "Fuera de los limites"
					return False
			else:
				if ((n+1) > self.cantX): 
					#print "Fuera de los limites"
					return False

			#print "testeando posicion correcta",n,p
			if (self.start == None) and (self.end == None):
				#print "No hay start o end"
				return True
			#print "# chequea que no este ocupada esa posicion"
			if (self.values[n][p].value != -1):
				#print "N,P ocupada"
				return False
			#print "# chequear la otra posicion ocupada por la pieza, segun este vertical u horizontal"
			try: 
				if (dominoPiece.vertical):
					if (self.values[n][p+1].value != -1):
						#print "N,P+1 ocupada"
						return False
				else:
					if (self.values[n+1][p].value != -1):
						#print "N+1,P ocupada"
						return False

			except (IndexError),e:		
				#print "Fuera de rango * (1) test_good_position"
				return False

			#print "# chequear las posiciones laterales"
			valueA = dominoPiece.a
			valueB = dominoPiece.b
			if dominoPiece.reversed:
				valueA = dominoPiece.b
				valueB = dominoPiece.a

			bad = self._test_invalid(valueA,n,p)
			if dominoPiece.vertical:
				bad = bad or self._test_invalid(valueB,n,p+1)
			else:
				bad = bad or self._test_invalid(valueB,n+1,p)
			if bad:
				#print "BAD posiciones laterales"
				return False 

			#print "# hago test contra start"
			ok = self.test_valid(self.start,valueA,n,p)
			if ok:
				n2,p2 = self._get_oposite_corner(dominoPiece,n,p,n,p)
				value2 = valueB
			else:		
				if dominoPiece.vertical:
					ok = ok or self.test_valid(self.start,valueB,n,p+1)
				else:
					ok = ok or self.test_valid(self.start,valueB,n+1,p)
				if ok:
					n2,p2 = n,p
					value2 = valueA
			if ok:
				#print "Coincide start",n2,p2,value2
				if self.start == None: 
					self.start = Tile(n2,p2)			
				self.start.n,self.start.p = n2,p2
				self.start.value = value2
				self.start.piece = dominoPiece
				return True	

		
			#print "# hago test contra end"
			ok = self.test_valid(self.end,valueA,n,p)
			if ok:
				n2,p2 = self._get_oposite_corner(dominoPiece,n,p,n,p)
				value2 = valueB
			else:	
				if dominoPiece.vertical:
					ok = ok or self.test_valid(self.end,valueB,n,p+1)
				else:
					ok = ok or self.test_valid(self.end,valueB,n+1,p)
				if ok:
					n2,p2 = n,p
					value2 = valueA
			if ok:
				#print "Coincide end",n2,p2,value2
				if self.end == None:
					self.end = Tile(n2,p2)
				self.end.n,self.end.p = n2,p2
				self.end.value = value2
				self.end.piece = dominoPiece
				return True	
		except (IndexError),e:		
			print "Fuera de rango * test_good_position"
		#print "End test False"

		return False

	def _get_oposite_corner(self,piece,nPiece,pPiece,nTest,pTest):	
		if (nPiece == nTest) and (pPiece == pTest):
			if piece.vertical:
				return nPiece,pPiece+1
			else:
				return nPiece+1,pPiece
		else:
			return nPiece,pPiece

	

	def _test_invalid(self,value,n,p):
		#print "test invalid value",value,"n=",n,"p=",p
		try:
			if (self.values[n+1][p].value != -1) and (self.values[n+1][p].value != value):
				return True
			if (self.values[n-1][p].value != -1) and (self.values[n-1][p].value != value):
				return True
			if (self.values[n][p+1].value != -1) and (self.values[n][p+1].value != value):
				return True
			if (self.values[n][p-1].value != -1) and (self.values[n][p-1].value != value):
				return True
		#	if (n+1 < self.cantX):
		#		if (self.values[n+1][p].value != -1) and (self.values[n+1][p].value != value):
		#			return True
		#	if (n-1 >= 0):
		#		if (self.values[n-1][p].value != -1) and (self.values[n-1][p].value != value):
		#			return True
		#	if (p+1 < self.cantY):			
		#		if (self.values[n][p+1].value != -1) and (self.values[n][p+1].value != value):
		#			return True
		#	if (p-1 >= 0):
		#		if (self.values[n][p-1].value != -1) and (self.values[n][p-1].value != value):
		#			return True
		except (IndexError),e:		
			print "index error _test_invalid"	
		return False

	def test_valid(self,tile,value,n,p):
		if (tile == None):
			return False
		# no anda bien y hay que chequear contra start y end
		#print "test valid n=",n,"p=",p,"value", value
		#print "tile n",tile.n,"p",tile.p,"value",tile.value

		if (tile.n == n-1) and (tile.p == p):
			return (tile.value == value)
		if (tile.n == n+1) and (tile.p == p):
			return (tile.value == value)
		if (tile.n == n) and (tile.p-1 == p):
			return (tile.value == value)
		if (tile.n == n) and (tile.p+1 == p):
			return (tile.value == value)

		return False

	def _create_domino(self):
		for n in range(0,7):
			for p in range(n,7):
				#creo pieza
				piece = DominoPiece(n,p)
				self.pieces.append(piece)
		self.processor.alter_labels(self.pieces)

	# Toma al azar una cantidad de piezas del juego y las devuelve en una coleccion
	def take_pieces(self,cant):
		result = []
		for n in range(0,cant):
			cantPieces = len(self.pieces) 
			if (cantPieces > 0):
				r = int(random.random() * cantPieces)
				piece =  self.pieces[r]
				# la quito de las piezas del juego 
				self.pieces[r] = cantPieces
				self.pieces.remove(cantPieces)
				# la agrego a result
				result.append(piece)
		return result

	# para debug
	def print_value_pieces(self,pieceList):
		print "printValues"
		for n in range(0,len(pieceList)):
			piece = pieceList[n]
			print piece.n,piece.p

	def start_game(self,numPlayers):
		self._create_domino()
		self.placed_pieces = []
		self.players = []
		auto_player = SimpleAutoPlayer(self,0)
		auto_player.set_pieces(self.take_pieces(7)) 
		self.players.append(auto_player)					
		for n in range(1,numPlayers):
			#print "bucle creacion jugadores",n
			player = DominoPlayer(self,n)
			player.set_pieces(self.take_pieces(7)) 
			self.players.append(player)					

		# comienza a jugar el primer jugador
		self.players[0].play()
		self.ui_player = self.players[1]
		self.ui_player.color = profile.get_color()
		self.ui_player.name = profile.get_nick_name()


	def show_pieces_player(self,player):
		pieces = player.get_pieces()

		if (len(pieces) > 0):
			separacion_x = int((dominoview.SCREEN_WIDTH - dominoview.SIZE * len(pieces)) / len(pieces))
			x = separacion_x / 2
			y = self.table.limitTable + 5

			for n in range(0,len(pieces)):
				piece = pieces[n]
				piece.x = x
				piece.y = y
				piece.vertical = True
			
				x = x + dominoview.SIZE + separacion_x
				piece.visible = True
	

	def get_status(self):
		players_status = ''
		for n in range(0,len(self.players)):
			player = self.players[n]
			players_status = players_status + player.get_status()

		if (len (self.pieces) > 0):
			players_status = players_status + _("Stack")+" : " + str(len(self.pieces))
		return players_status


class DominoGamePoints:

	def __init__(self):
		self.name = None
		self.played = 0
		self.win = 0
		self.lost = 0

