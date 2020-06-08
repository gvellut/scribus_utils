# -*- coding: utf-8 -*-

import codecs
import os
import re
import sys
import xml.etree.ElementTree as ET

try:
    import scribus as sc
except Exception:

    class ScribusProxy(object):
        def __getattr__(self, name):
            if name == "messageBox":

                def _messageBox(*args, **kwargs):
                    print "MessageBox %s" % args[1]

                return _messageBox

            def _missing(*args, **kwargs):
                print "%s * %r ** %r" % (name, args, kwargs)

            return _missing

    sc = ScribusProxy()


# TODO tester linked frames

KEY_PREFIX = "#---"
COPY_PREFIX = "Copy of "
NO_STYLE = "Default Paragraph Style"
DEBUG = True

# spaces : snb sen sem stn stk  smi sha
# dashes : dem den
ENTITIES = {
    "snb": u"\u00A0",  # non breaking
    "sen": u"\u2002",  # en space
    "sem": u"\u2003",  # em space
    "stn": u"\u2009",  # thin
    "stk": u"\u2004",  # thick 1/3
    "smi": u"\u2005",  # mid 1/4
    "sha": u"\u200A",  # hair
    "dem": u"\u2014",  # em dash
    "den": u"\u2013",  # en dash
    "hsf": u"\u00AD",  # soft hyphen
}
XML_ENTITIES = set(["lt", "gt", "amp", "quot"])

# __file__ is not defined when running from Scribus but the dir of
# the script being executed is in sys.path 0
data_file = os.path.join(sys.path[0], "test_data.txt")


def prep():
    paragraph_styles = set(sc.getParagraphStyles())
    char_styles = set(sc.getCharStyles())
    return paragraph_styles, char_styles


def read_data(data_file):
    with codecs.open(data_file, encoding="utf-8") as f:
        data = f.read()

    def wrapup(content):
        # remove empty lines at the beginning and end
        content_clean = []
        for i, c in enumerate(content):
            if len(c) != 0:
                content_clean = content[i:]
                break
        for i, c in enumerate(reversed(content_clean)):
            if len(c) != 0:
                content_clean = content_clean[: len(content_clean) - i]
                break
        return (
            u"<text><paragraph>%s</paragraph></text>"
            % u"</paragraph><paragraph>".join(content_clean)
        )

    lines = data.splitlines()
    texts = {}
    key = None
    content = None
    for line in lines:
        if line.startswith(KEY_PREFIX):
            if key:
                texts[key] = wrapup(content)
            key = line[len(KEY_PREFIX) :].strip()
            content = []
        else:
            line = line.strip()
            if not key:
                print u"No key defined for %s" % line
                continue
            content.append(line)
    if key:
        texts[key] = wrapup(content)
    return texts


def add_text(key, text, pstyles, cstyles):
    sc.selectText(0, 0, key)
    sc.deleteText(key)

    errors = []

    text_ent = _process_entities(text)
    root = ET.fromstring(text_ent.encode("utf-8"))
    cursor_pos = 0
    current_style = NO_STYLE
    for p in root:
        if p.text:
            sc.insertText(p.text, -1, key)
            cursor_pos += len(p.text)

        for s in p:
            if s.tag == "t":
                if not s.text:
                    errors.append(u"t tags should have text")
                else:
                    t = s.text
                    sc.insertText(t, -1, key)
                    cursor_pos += len(t)

                    rt_l = cursor_pos - len(t)
                    sc.selectText(rt_l, -1, key)
                    if "f" in s.attrib:
                        font_name = s.attrib["f"]
                        try:
                            sc.setFont(s.attrib["f"], key)
                        except Exception:
                            errors.append(u"Invalid font name: %s" % font_name)
                    if "c" in s.attrib:
                        # not currently defined color name will be added with
                        # a brown color
                        # TODO but no way to tell ?
                        c = s.attrib["c"]
                        sc.setTextColor(c, key)
                    if "s" in s.attrib:
                        font_size = s.attrib["s"]
                        try:
                            sc.setFontSize(int(font_size), key)
                        except Exception:
                            errors.append(u"Invalid font size: %s" % font_size)
                    sc.selectText(0, 0, key)  # deselect

            elif s.tag == "cs":
                if not s.text:
                    errors.append(u"cs tags should have text")
                else:
                    t = s.text
                    sc.insertText(t, -1, key)
                    cursor_pos += len(t)

                    rt_l = cursor_pos - len(t)
                    sc.selectText(rt_l, -1, key)
                    if "n" in s.attrib:
                        # TODO check if in current styles ?
                        char_style = s.attrib["n"]
                        sc.setCharacterStyle(char_style, key)
                    else:
                        errors.append(u"cs tags should have a 'n' attribute")
                    sc.selectText(0, 0, key)  # deselect

            elif s.tag == "ps":
                # change the state of the current style for this paragraph
                # and the following
                if "n" in p[0].attrib:
                    # TODO check if in current styles ?
                    current_style = p[0].attrib["n"]
                    if not current_style:
                        current_style = NO_STYLE
                else:
                    errors.append(u"ps tags should have a 'n' attribute")
                if s.text:
                    errors.append(u"ps tags should not have text")

            # text as is
            if s.tail:
                t = s.tail
                sc.insertText(t, -1, key)
                cursor_pos += len(t)

        sc.insertText("\r", -1, key)
        cursor_pos += 1
        sc.selectText(cursor_pos - 1, -1, key)
        sc.setStyle(current_style, key)
        sc.selectText(0, 0, key)  # deselect

    if errors:
        _error(u"Errors while processing '%s':\n- %s" % (key, "\n- ".join(errors)))


entity_rex = re.compile(r"(&(\w+?);)", flags=re.IGNORECASE)


def _process_entities(text):
    def repl(mat):
        ent = mat.group(2)
        if ent in ENTITIES:
            return ENTITIES[mat.group(2)]
        elif ent in XML_ENTITIES or ent.startswith("#x"):
            return mat.group(1)
        else:
            return "??"

    return re.sub(entity_rex, repl, text)


def _debug(o):
    if DEBUG:
        sc.messageBox("DEBUG", repr(o))


def _error(o, icon=sc.ICON_WARNING):
    result = sc.messageBox(
        "ERROR", o, icon, sc.BUTTON_OK | sc.BUTTON_DEFAULT, sc.BUTTON_ABORT,
    )
    if result == sc.BUTTON_ABORT:
        sys.exit(1)


def _index_items_by_page():
    pass


def main(argv):
    if not sc.haveDoc():
        _error(u"Need a document", sc.ICON_CRITICAL)
        sys.exit(1)

    pstyles, cstyles = prep()
    texts = read_data(data_file)
    # _debug(texts)

    sc.setRedraw(False)

    # TODO index items for pages
    _index_items_by_page()

    num_selected = sc.selectionCount()
    if num_selected:
        for i in range(num_selected):
            key = sc.getSelectedObject(i)
            if sc.getObjectType(key) != "TextFrame":
                _error(u"Selected object with name %s not a text frame" % key)
                continue
            # TODO process pages later
            if key not in texts:
                _error(u"Selected text frame with name %s not in data" % key)
                continue

            add_text(key, texts[key], pstyles, cstyles)
    else:
        # go through the texts keys
        sc.progressTotal(len(texts))
        progress = 0
        try:
            for key, text in texts.items():
                progress += 1
                sc.progressSet(progress)
                # TODO process pages later
                if key.startswith("#"):
                    continue

                # TODO keep around ? and display at the end ?
                if not sc.objectExists(key):
                    _error(u"Object %s from data not found" % key)
                    continue
                if sc.getObjectType(key) != "TextFrame":
                    _error(u"Object %s from data not a text frame" % key)
                    continue

                add_text(key, texts[key], pstyles, cstyles)
        finally:
            sc.deselectAll()


def main_wrapper(argv):
    try:
        sc.statusMessage(u"Running script...")
        sc.progressReset()
        main(argv)
    finally:
        if sc.haveDoc():
            sc.setRedraw(True)
        sc.statusMessage(u"Done")
        sc.progressReset()
        # TODO no effect ? How to keep the asterisk ? appears then disappears
        sc.docChanged(True)


if __name__ == "__main__":
    main_wrapper(sys.argv)
    # texts = read_data(data_file)
    # print (repr(texts))

    # xml = u'<text><paragraph><ps n="My Style" />Hell&gt;o &dem; World.</paragraph><paragraph></paragraph><paragraph>Second line <t s="24">with</t> My Style</paragraph><paragraph><ps n="" />This line has no style <t f="Times New Roman" s="18" c="Red" >but has</t> char styles and <cs n="superscript">font</cs> change</paragraph></text>'
    # add_text("TEST", xml, set(), set())
