#!/usr/bin/env python

### Piezas del domino
### By Gonzalo Odiard, 2006 godiard at gmail.com
### GPL License - http://www.gnu.org/copyleft/gpl.html


import gobject
import gtk
import cairo
import rsvg

import pygtk
pygtk.require('2.0')
import getopt

import logging
from gettext import gettext as _
import sugar
from sugar.graphics.icon import Icon

import cairoutils


# SIZE Es el ancho de una ficha (y la mitads del largo)
# podemos imaginar el tablero dividido en cuadrados de lado SIZE
SIZE = 60
# Si se quiere usar fichas mas grandes, se puede usar SIZE = 70 y cambiar _drawLabel el scale = 3


SCREEN_HEIGHT = gtk.gdk.screen_height()
SCREEN_WIDTH = gtk.gdk.screen_width()


class Tile:

	"""
	Informacion de cada posicion del tablero
	"""

	def __init__ (self,n,p):
		self.n = n
		self.p = p
		self.value = -1
		self.piece = None

class DominoTableView():

	""" 
	Dibuja una grilla sobre la que se van a poner las fichas
	Ademas tiene metodos para saber a que casillero corresponde una posicion del mouse 
	o donde ubicar una ficha
	"""

	__gtype_name__ = 'DominoTableView'

	def __init__(self,**kwargs):
		self.cantX = int(SCREEN_WIDTH / SIZE) - 1
		self.cantY = int( ( SCREEN_HEIGHT - (SIZE*3.5) ) / SIZE )
		self.margenX = int ((SCREEN_WIDTH - SIZE * self.cantX) /2)
		self.limitTable = SIZE * self.cantY
		print "Table cantX",self.cantX,"cantY",self.cantY


	def paint(self,ctx):

		# agrego 2,2 para que la grilla quede en la base de las piezas (por la perspectiva)
		alto = 5
		ctx.move_to(alto, alto)

		ctx.rectangle(self.margenX + alto, 0 + alto, SIZE * self.cantX + alto, SIZE * (self.cantY) + alto)
		ctx.set_source_rgb (204.0/255.0, 204.0/255.0, 204.0/255.0)
		ctx.fill()


		ctx.set_line_width(1)
		ctx.set_source_rgb (1, 1, 0)

		for n in range(0,self.cantY+1):
			ctx.move_to(self.margenX + alto, n * SIZE + alto)
			ctx.line_to(SCREEN_WIDTH - self.margenX + alto,n*SIZE + alto)
			ctx.stroke()
			
		ctx.move_to(0, 0)
		for n in range(0,self.cantX+1):
			ctx.move_to(self.margenX + n * SIZE + alto, 0 + alto)
			ctx.line_to(self.margenX + n * SIZE + alto , self.limitTable + alto)
			ctx.stroke()
		
	def get_tile_position(self,n,p):
		return self.margenX + n * SIZE, (p-1) * SIZE

	def get_tile_coord(self,x,y):
		return (x - self.margenX) / SIZE, (y / SIZE) +1

	def show_status(self,ctx,text):

		xIni = 10
		yIni = 5
	
		stroke_r,stroke_g,stroke_b = 0,0,0
		alpha = 0.6
		ctx.set_source_rgba (stroke_r,stroke_g,stroke_b,alpha)

		ctx.select_font_face ("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
		ctx.set_font_size (12)
		x_bearing, y_bearing, width, height, x_advance, y_advance = ctx.text_extents (text)

		radio = 16

		cairoutils.draw_round_rect(ctx,xIni, yIni, width + radio * 2, height * 2, radio)
		ctx.stroke()

		ctx.move_to (xIni + radio + x_bearing , yIni + height)
		ctx.show_text (text)
		#print "w", width, "h", height,"x_b",x_bearing,"y_b",y_bearing

	def show_scores(self,ctx,score_list):
		print "scores"
		alto = 5
		ctx.move_to(alto, alto)

		ctx.rectangle(self.margenX + alto, 0 + alto, SIZE * self.cantX + alto, SIZE * (self.cantY) + alto)
		ctx.set_source_rgb (204.0/255.0, 204.0/255.0, 204.0/255.0)
		ctx.fill()

		ctx.set_line_width(1)
		ctx.set_source_rgb (1, 1, 0)
		ctx.rectangle(self.margenX + alto, 0 + alto, SIZE * self.cantX + alto, SIZE * (self.cantY) + alto)
		ctx.stroke()	

		altoRenglon = 40

		stroke_r,stroke_g,stroke_b = 0,0,0
		alpha = 1
		ctx.set_source_rgb (stroke_r,stroke_g,stroke_b)

		ctx.select_font_face ("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
		ctx.set_font_size (30)

		
		x = self.margenX + 200
		y = altoRenglon * 2
		ctx.move_to (x,y)

		ctx.move_to (x+300,y)
		ctx.show_text (_("Played"))
		ctx.move_to (x+450,y)
		ctx.show_text (_("Win"))
		ctx.move_to (x+600,y)
		ctx.show_text (_("Lost"))
		y = y + altoRenglon
		ctx.move_to (x,y)

		for n in range(0,len(score_list)):
			game_points = score_list[n]
			ctx.show_text (game_points.name)			
			ctx.move_to (x+350,y)
			ctx.show_text (str(game_points.played))
			ctx.move_to (x+500,y)
			ctx.show_text (str(game_points.win))
			ctx.move_to (x+650,y)
			ctx.show_text (str(game_points.lost))
			y = y + altoRenglon
			ctx.move_to (x,y)
			


	def help(self,ctx):


		altoRenglon = 45
		x = self.margenX + 20
		y = altoRenglon * 4

		ctx.set_line_width(1)
		ctx.set_source_rgb (1, 1, 0)
		ctx.rectangle(self.margenX + 10, altoRenglon * 3, SIZE * self.cantX - 10, y + altoRenglon * 4)
		ctx.stroke()	


		stroke_r,stroke_g,stroke_b = 0,0,0
		alpha = 1
		ctx.set_source_rgb (stroke_r,stroke_g,stroke_b)

		ctx.select_font_face ("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
		ctx.set_font_size (30)
		#x_bearing, y_bearing, width, height, x_advance, y_advance = ctx.text_extents ("M")

		ctx.move_to (x,y)
		ctx.show_text (_("You can select a piece with the arrow keys and use it with enter."))

		y = y + altoRenglon
		ctx.move_to (x,y)
		ctx.show_text (_("When you selected the piece, you can move it to the place "))

		y = y + altoRenglon
		ctx.move_to (x,y)
		ctx.show_text (_("with the arrows , turn it with space and place it with enter."))
		
		y = y + altoRenglon
		ctx.move_to (x,y)
		ctx.show_text (_("If you want use another piece, press escape."))

		y = y + altoRenglon
		ctx.move_to (x+80,y)
		ctx.show_text (_("You can use the cursors to move too."))

		y = y + altoRenglon
		ctx.move_to (x+80,y)
		ctx.show_text (_("And use check to select, circle to rotate"))

		y = y + altoRenglon  
		ctx.move_to (x+80,y)
		ctx.show_text (_("and X to use another piece."))

		self.show_svg(ctx,"icons/cursors.svg",x,y - ( altoRenglon * 2.75))
		self.show_svg(ctx,"icons/gamekeys.svg",x,y - ( altoRenglon * 1.25))




	def show_svg(self,ctx,file_name,x,y):
		h = rsvg.Handle(file_name)
		surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100) 
		temp_ctx = cairo.Context(surf)
		h.render_cairo(temp_ctx)
		ctx.translate(x,y)
		ctx.set_source_surface(surf)
		ctx.paint()
		ctx.translate(-x,-y)
		


	def msg_end_game(self,ctx,win):

		#snippet_normalize (cr, width, height)
		ctx.select_font_face ("Sans", cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD)

		text = ""
		if (win):
			ctx.set_font_size (100)
			text = _("You win!!!")
		else:
			ctx.set_font_size (60)
			text = _("Sorry, you lost")

		x_bearing, y_bearing, width, height, x_advance, y_advance = ctx.text_extents (text)
		x = (SCREEN_WIDTH - width) / 2
		y = (SCREEN_HEIGHT - height) / 2
		ctx.move_to (x, y)

		ctx.text_path (text)
		ctx.set_source_rgb (0.5,0.5,1)
		ctx.fill_preserve ()
		ctx.set_source_rgb (0,0,0)
		ctx.set_line_width (2)
		ctx.stroke ()



