def draw_round_rect(context, x, y, w, h, r):
    # Copiado de http://www.steveanddebs.org/PyCairoDemo/
    # "Draw a rounded rectangle"
    #   A****BQ
    #  H      C
    #  *      *
    #  G      D
    #   F****E

    # Move to A
    context.move_to(x + r, y)
    # Straight line to B
    context.line_to(x + w - r, y)
    # Curve to C, Control points are both at Q
    context.curve_to(x + w, y, x + w, y, x + w, y + r)
    # Move to D
    context.line_to(x + w, y + h - r)
    # Curve to E
    context.curve_to(x + w, y + h, x + w, y + h, x + w - r, y + h)
    # Line to F
    context.line_to(x + r, y + h)
    # Curve to G
    context.curve_to(x, y + h, x, y + h, x, y + h - r)
    # Line to H
    context.line_to(x, y + r)
    # Curve to A
    context.curve_to(x, y, x, y, x + r, y)
    return
