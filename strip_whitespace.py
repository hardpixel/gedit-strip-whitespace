import gi, re

gi.require_version('Gedit', '3.0')

from gi.repository import GObject, Gedit


class StripWhitespaceWindowActivatable(GObject.Object, Gedit.WindowActivatable):

  window = GObject.property(type=Gedit.Window)

  def __init__(self):
    GObject.Object.__init__(self)

    self._document   = None
    self._handler_id = None

  def do_activate(self):
    self._handler_id = self.window.connect('tab-added', self.on_tab_added)

  def do_deactivate(self):
    self.window.disconnect(self._handler_id)

  def on_tab_added(self, window, tab, data=None):
    self._document = tab.get_document()
    self._document.connect('save', self.on_document_save)

  def on_document_save(self, document, data=None):
    self._document.begin_user_action()
    self.strip_trailing_spaces()
    self.strip_eof_newlines()
    self._document.end_user_action()

  def strip_trailing_spaces(self):
    line   = 0
    lmatch = 0

    itstart = self._document.get_start_iter()
    itend   = self._document.get_end_iter()

    text  = self._document.get_text(itstart, itend, False)
    regex = re.compile('.*?([ \t]+)$', flags=re.MULTILINE)

    for match in re.finditer(regex, text):
      line += text.count('\n', lmatch, match.start())

      wsstart = match.start(1) - match.start()
      wsend   = match.end(1) - match.start()

      itstart.set_line(line)
      itstart.set_line_offset(wsstart)

      itend.set_line(line)
      itend.set_line_offset(wsend)

      self._document.delete(itstart, itend)

      lmatch = match.end()

  def strip_eof_newlines(self):
    itend = self._document.get_end_iter()

    if itend.starts_line():
      while itend.backward_char():
        if not itend.ends_line():
          itend.forward_to_line_end()
          break

      self._document.delete(itend, self._document.get_end_iter())
      self._document.insert(self._document.get_end_iter(), "\n")
