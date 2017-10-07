import gi, re

gi.require_version('Gedit', '3.0')

from gi.repository import GObject, Gedit


class StripWhitespaceWindowActivatable(GObject.Object, Gedit.WindowActivatable):

  window = GObject.property(type=Gedit.Window)

  def __init__(self):
    GObject.Object.__init__(self)

    self._handler_id = None
    self._document   = None

  def do_activate(self):
    self._handler_id = self.window.connect('tab-added', self.on_tab_added)

  def do_deactivate(self):
    self.window.disconnect(self._handler_id)

  def on_tab_added(self, window, tab, data=None):
    self._document = tab.get_document()
    self._document.connect('save', self.on_document_save)

  def on_document_save(self, document, data=None):
    self.strip_trailing_spaces()
    self.strip_eof_newlines()

  def strip_trailing_spaces(self):
    text = self._document.get_text(self._document.get_start_iter(), self._document.get_end_iter(), False)
    compiledpattern = re.compile('.*?([ \t]+)$', flags=re.MULTILINE)

    start_iter = self._document.get_start_iter()
    end_iter   = self._document.get_start_iter()

    line_no        = 0 # Last matched line no
    last_match_pos = 0 # Last matched position in the string

    for match in re.finditer(compiledpattern, text):
      # Count the newlines since the last match
      line_no += text.count('\n', last_match_pos, match.start())

      # Work out the offsets within the line
      whitespace_start = match.start(1) - match.start()
      whitespace_end   = match.end(1) - match.start()

      # Update the iterators and do the deletion
      start_iter.set_line(line_no)
      start_iter.set_line_offset(whitespace_start)

      end_iter.set_line(line_no)
      end_iter.set_line_offset(whitespace_end)

      self._document.delete(start_iter, end_iter)

      # Update the last match position
      last_match_pos = match.end()

  def strip_eof_newlines(self):
    itr = self._document.get_end_iter()

    if itr.starts_line():
      while itr.backward_char():
        if not itr.ends_line():
          itr.forward_to_line_end()
          break

      self._document.delete(itr, self._document.get_end_iter())
      self._document.insert(self._document.get_end_iter(), "\n")
