import gobject
import gtk
import cairo


def draw_round_rect(context,x,y,w,h,r):
	# Copiado de http://www.steveanddebs.org/PyCairoDemo/
	# "Draw a rounded rectangle"
	#   A****BQ
	#  H      C
	#  *      *
	#  G      D
	#   F****E

	context.move_to(x+r,y)                      # Move to A
	context.line_to(x+w-r,y)                    # Straight line to B
	context.curve_to(x+w,y,x+w,y,x+w,y+r)       # Curve to C, Control points are both at Q
	context.line_to(x+w,y+h-r)                  # Move to D
	context.curve_to(x+w,y+h,x+w,y+h,x+w-r,y+h) # Curve to E
	context.line_to(x+r,y+h)                    # Line to F
	context.curve_to(x,y+h,x,y+h,x,y+h-r)       # Curve to G
	context.line_to(x,y+r)                      # Line to H
	context.curve_to(x,y,x,y,x+r,y)             # Curve to A
	return

