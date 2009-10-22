import gobject
import gtk
import cairo
import pango
import math, random

import pygtk
pygtk.require('2.0')
import getopt

import logging
from gettext import gettext as _

import sugar
from sugar.graphics import style
import dominoview

M_PI = 3.14159265358979323846 

class PieceProcessorMathSimple:

	"""
	Este es el primer ejemplo de PieceProccesor
	Altera los valores de textA y textB de la pieza y la dibuja 

	"""

	def get_name(self):
		return _("Simple")

	def alter_labels(self,pieces):
		for n in range(0,len(pieces)):
			piece = pieces[n]
			# altero textA
			if (random.random() > .5):
				r = int(random.random() * 10)
				if (r < piece.a):
					piece.textA = str(piece.a - r) + "+" + str(r)
				else:
					piece.textA = str(r) + "-" + str(r - piece.a)
			# altero textB
			if (random.random() > .5):
				r = int(random.random() * 10)
				if (r < piece.b):
					piece.textB = str(piece.b - r) + "+" + str(r)
				else:
					piece.textB = str(r) + "-" + str(r - piece.b)
		

	def draw_label(self,ctx,piece,text,xIni,yIni):
		#print "Dibujando ",text
		stroke_r,stroke_g,stroke_b = 0,0,0
		alpha = 1
		if (piece.player.color != None):
			xocolor = piece.player.color
			stroke_r,stroke_g,stroke_b,alpha = style.Color(xocolor.get_stroke_color(),1.0).get_rgba()
		ctx.set_source_rgb (stroke_r,stroke_g,stroke_b)

		ctx.select_font_face ("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
		ctx.set_font_size (20)
		x_bearing, y_bearing, width, height, x_advance, y_advance = ctx.text_extents (text)
		x = 0.5-(width/2 + x_bearing)
		y = 0.5-(height/2 + y_bearing)
		ctx.move_to (xIni+x+(dominoview.SIZE/2), yIni+y+(dominoview.SIZE/2))
		ctx.show_text (text)



class PieceProcessorProductTable:

	def __init__(self,n):
		self.product = n

	def get_name(self):
		return _("Table of")+" "+str(self.product)

	"""
	Este es un procesor para las tablas de multiplicar
	Altera los valores de textA y textB de la pieza y la dibuja 

	"""

	def alter_labels(self,pieces):
		for n in range(0,len(pieces)):
			piece = pieces[n]
			# altero textA
			if (random.random() > .5):
				piece.textA = str((piece.a+2) * self.product) 
			else:
				piece.textA = str((piece.a+2)) + "*" + str(self.product)
			# altero textB
			if (random.random() > .5):
				piece.textB = str((piece.b+2) * self.product)
			else:
				piece.textB = str((piece.b+2)) + "*" + str(self.product)
		

	def draw_label(self,ctx,piece,text,xIni,yIni):
		#print "Dibujando ",text
		stroke_r,stroke_g,stroke_b = 0,0,0
		
		alpha = 1
		if (piece.player.color != None):
			xocolor = piece.player.color
			stroke_r,stroke_g,stroke_b,alpha = style.Color(xocolor.get_stroke_color(),1.0).get_rgba()
		ctx.set_source_rgb (stroke_r,stroke_g,stroke_b)

		ctx.select_font_face ("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
		ctx.set_font_size (20)
		x_bearing, y_bearing, width, height, x_advance, y_advance = ctx.text_extents (text)
		x = 0.5-(width/2 + x_bearing)
		y = 0.5-(height/2 + y_bearing)
		ctx.move_to (xIni+x+(dominoview.SIZE/2), yIni+y+(dominoview.SIZE/2))
		ctx.show_text (text)


class PieceProcessorFractions:

	"""
	Este es un PieceProccesor que dibuja fracciones en forma numerica y grafica
	vamos a trabajar con: 
	0
	1/6
	2/6 = 1/3
	3/6 = 1/2 = 2/4
	4/6 = 2/3
	5/6
	6/6 = 1 = 2/2 = 3/3
    A su vez se puede mostrar en forma grafica o en forma numerica 
	textA lo voy a representar siempre numericamente y textB lo voy a representar graficamente

	"""

	def get_name(self):
		return _("Fractions")

	def alter_labels(self,pieces):
		for n in range(0,len(pieces)):
			piece = pieces[n]
			# altero textA
			piece.textA = self.alter_label(piece.a)
			# pongo una G al comienzo para saber 
			# que las tengo que representar graficamente
			piece.textB = "G"+self.alter_label(piece.b)

	def alter_label(self,val):
		if (val == 0):
			return "0"
		elif (val == 1):
			return "1/6"
		elif (val == 2):
			if (random.random() > .5):
				return "2/6"
			else:
				return "1/3"
		elif (val == 3):
			rand = random.random()			
			if (rand < .33):
				return "3/6"
			elif (rand < .66):
				return "1/2"
			else:
				return "2/4"
		elif (val == 4):
			if (random.random() > .5):
				return "4/6"
			else:
				return "2/3"
		elif (val == 5):
			return "5/6"
		elif (val == 6):
			rand = random.random()			
			if (rand < .25):
				return "6/6"
			elif (rand < .5):
				return "3/3"
			elif (rand < .75):
				return "2/2"
			else:
				return "1"


	def draw_label(self,ctx,piece,text,xIni,yIni):

		stroke_r,stroke_g,stroke_b = 0,0,0
		border_r,border_g,border_b = 0.5,0.5,0.5

		alpha = 1
		if (piece.player.color != None):
			xocolor = piece.player.color
			stroke_r,stroke_g,stroke_b,alpha = style.Color(xocolor.get_stroke_color(),1.0).get_rgba()
			#border_r,border_g,border_b,aplha = style.Color(xocolor.get_fill_color(),1.0).get_rgba()
		ctx.set_source_rgb (stroke_r,stroke_g,stroke_b)

		if (text[0] != "G"):
			#print "Dibujando ",text
			ctx.select_font_face ("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
			ctx.set_font_size (20)
			x_bearing, y_bearing, width, height, x_advance, y_advance = ctx.text_extents (text)
			x = 0.5-(width/2 + x_bearing)
			y = 0.5-(height/2 + y_bearing)
			ctx.move_to (xIni+x+(dominoview.SIZE/2), yIni+y+(dominoview.SIZE/2))
			ctx.show_text (text)
		else:
			text = text[1:]
			xCenter = xIni+(dominoview.SIZE/2)
			yCenter = yIni+(dominoview.SIZE/2)
			radio = 22
			ctx.set_line_width(2)

			if ((text == "0") or (text == "1")):
				ctx.move_to (xCenter + radio , yCenter)
 				ctx.arc (xCenter, yCenter, radio, 0, 2*M_PI)	
				if (text == "0"):
					ctx.stroke()
				if (text == "1"):
					ctx.fill_preserve()
			else:
				numerador = int(text[0])
				denominador = int(text[2])
				ctx.move_to (xCenter, yCenter)
				angulo_porcion = 2 * M_PI / denominador
				angulo_inicial = 0
				#print "numerador",numerador,"denominador",denominador,"angulo_porcion",angulo_porcion
				# relleno las fracciones del numerador
				for n in range(0,numerador):
					xIni = math.cos(angulo_inicial) * radio
					yIni = math.sin(angulo_inicial) * radio
					#print "N",n,"xIni",xIni,"yIni",yIni
					ctx.line_to (xCenter + xIni, yCenter + yIni)
					ctx.arc (xCenter, yCenter, radio, angulo_inicial, angulo_inicial + angulo_porcion)	
					ctx.line_to (xCenter, yCenter)
					ctx.close_path()
					ctx.set_source_rgb (stroke_r,stroke_g,stroke_b)
					ctx.fill()
					angulo_inicial = angulo_inicial + angulo_porcion
	
				# pinto los bordes
				ctx.move_to (xCenter, yCenter)
				angulo_porcion = 2 * M_PI / denominador
				angulo_inicial = 0
				#print "numerador",numerador,"denominador",denominador,"angulo_porcion",angulo_porcion
				ctx.set_source_rgb (border_r,border_g,border_b)
				for n in range(0,denominador):
					xIni = math.cos(angulo_inicial) * radio
					yIni = math.sin(angulo_inicial) * radio
					#print "N",n,"xIni",xIni,"yIni",yIni
					ctx.line_to (xCenter + xIni, yCenter + yIni)
					ctx.arc (xCenter, yCenter, radio, angulo_inicial, angulo_inicial + angulo_porcion)	
					ctx.line_to (xCenter, yCenter)
					ctx.close_path()
					ctx.stroke()
					angulo_inicial = angulo_inicial + angulo_porcion
	


class PieceProcessorPoints:

	"""
	Este es un PieceProccesor que dibuja los valores con puntos
	Es interesante ver como seria un caso en 
	el que no sea texto lo que pongamos sino imagenes 

	"""

	def get_name(self):
		return _("Points")

	def alter_labels(self,pieces):
		print "No hace nada"
		

	def draw_label(self,ctx,piece,text,xIni,yIni):

		stroke_r,stroke_g,stroke_b = 0,0,0
		alpha = 1
		if (piece.player.color != None):
			xocolor = piece.player.color
			stroke_r,stroke_g,stroke_b,alpha = style.Color(xocolor.get_stroke_color(),1.0).get_rgba()
		ctx.set_source_rgb (stroke_r,stroke_g,stroke_b)

		xCenter = xIni+(dominoview.SIZE/2)
		yCenter = yIni+(dominoview.SIZE/2)

		separa = (dominoview.SIZE/4)
		radio = 4

		#
		#   *1    *2
		#   *3 *4 *5
		#   *6    *7  
		#
		
		# 1
		if (text == "2") or (text == "3") or (text == "4") or (text == "5") or (text == "6"):
			ctx.arc (xCenter-separa, yCenter-separa, radio, 0, 2*M_PI)	
			ctx.fill ()
		# 2
		if (text == "4") or (text == "5") or (text == "6"):
			ctx.arc (xCenter+separa, yCenter-separa, radio, 0, 2*M_PI)	
			ctx.fill ()

		# 3
		if (text == "6"):
			ctx.arc (xCenter-separa, yCenter, radio, 0, 2*M_PI)	
			ctx.fill ()

		#4
		if (text == "1") or (text == "3") or (text == "5"):
			ctx.arc (xCenter, yCenter, radio, 0, 2*M_PI)	
			ctx.fill ()

		# 5
		if (text == "6"):
			ctx.arc (xCenter+separa, yCenter, radio, 0, 2*M_PI)	
			ctx.fill ()

		# 6
		if (text == "4") or (text == "5") or (text == "6"):
			ctx.arc (xCenter-separa, yCenter+separa, radio, 0, 2*M_PI)	
			ctx.fill ()

		# 7
		if (text == "2") or (text == "3") or (text == "4") or (text == "5") or (text == "6"):
			ctx.arc (xCenter+separa, yCenter+separa, radio, 0, 2*M_PI)	
			ctx.fill ()

