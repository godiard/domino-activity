from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import GObject

from sugar3.graphics.palette import Palette, ToolInvoker
from sugar3.graphics.palettemenu import PaletteMenuBox
from sugar3.graphics.palettemenu import PaletteMenuItem
from sugar3.graphics import style
from sugar3.graphics.icon import Icon


class PaletteBox(Gtk.ToolItem):

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_LAST, None, ([])), }

    def __init__(self, default, options):
        self._palette_invoker = ToolInvoker()
        Gtk.ToolItem.__init__(self)
        self._label = Gtk.Label()
        bt = Gtk.Button('')
        bt.set_can_focus(False)
        bt.remove(bt.get_children()[0])
        self._box = Gtk.HBox()
        bt.add(self._box)
        self._icon = Icon(icon_name='')
        self._box.pack_start(self._icon, False, False, 5)
        self._box.pack_end(self._label, False, False, 5)
        self.add(bt)
        self.show_all()

        # theme the button, can be removed if add the style to the sugar css
        if style.zoom(100) == 100:
            subcell_size = 15
        else:
            subcell_size = 11
        radius = 2 * subcell_size
        theme = "GtkButton {border-radius: %dpx;}" % radius
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(theme)
        style_context = bt.get_style_context()
        style_context.add_provider(css_provider,
                                   Gtk.STYLE_PROVIDER_PRIORITY_USER)

        # init palette
        self._hide_tooltip_on_click = True
        self._palette_invoker.attach_tool(self)
        self._palette_invoker.props.toggle_palette = True

        self.palette = Palette(_('Select option'))
        self.palette.set_invoker(self._palette_invoker)

        # load the fonts in the palette menu
        self._menu_box = PaletteMenuBox()
        self.props.palette.set_content(self._menu_box)
        self._menu_box.show()

        for option in options:
            if option.__class__ is str:
                self._add_menu(option, activate_cb=self.__option_selected_cb)
            else:
                self._add_menu(option[0], icon=option[1],
                               activate_cb=self.__option_selected_cb)

        self.set_value(default)

    def _set_icon(self, icon_name):
        self._box.remove(self._box.get_children()[0])
        self._icon = Icon(icon_name=icon_name,
                          pixel_size=style.STANDARD_ICON_SIZE)
        self._icon.show()
        self._box.pack_start(self._icon, False, False, 5)

    def __option_selected_cb(self, menu, option):
        self.set_value(option)
        self.emit('changed')

    def _add_menu(self, option, icon=None, activate_cb=None):
        if icon is not None:
            menu_item = PaletteMenuItem(icon_name=icon)
            if activate_cb is not None:
                menu_item.connect('activate', activate_cb, [option, icon])
        else:
            menu_item = PaletteMenuItem()
            if activate_cb is not None:
                menu_item.connect('activate', activate_cb, option)
        menu_item.set_label(option)
        self._menu_box.append_item(menu_item)
        menu_item.show()

    def __destroy_cb(self, icon):
        if self._palette_invoker is not None:
            self._palette_invoker.detach()

    def create_palette(self):
        return None

    def get_palette(self):
        return self._palette_invoker.palette

    def set_palette(self, palette):
        self._palette_invoker.palette = palette

    palette = GObject.property(
        type=object, setter=set_palette, getter=get_palette)

    def get_palette_invoker(self):
        return self._palette_invoker

    def set_palette_invoker(self, palette_invoker):
        self._palette_invoker.detach()
        self._palette_invoker = palette_invoker

    palette_invoker = GObject.property(
        type=object, setter=set_palette_invoker, getter=get_palette_invoker)

    def set_value(self, value):
        self._value = value
        if value.__class__ is str:
            self._label.set_text(value)
        else:
            self._label.set_text(value[0])
            self._set_icon(value[1])

    def get_value(self):
        return self._value
