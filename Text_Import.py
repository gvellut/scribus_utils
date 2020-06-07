# -*- coding: utf-8 -*-

import os
import sys
import xml.etree.ElementTree as ET

import scribus as sc

# TODO tester linked frames

KEY_PREFIX = "#---"
COPY_PREFIX = "Copy of "
NO_STYLE = "Default Paragraph Style"
DEBUG = True

# __file__ is not defined when running from Scribus but the dir of
# the script being executed is in sys.path 0
data_file = os.path.join(sys.path[0], "test_data.txt")


def prep():
    paragraph_styles = set(sc.getParagraphStyles())
    char_styles = set(sc.getCharStyles())
    return paragraph_styles, char_styles


def read_data(data_file):
    with open(data_file) as f:
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
            "<text><paragraph>%s</paragraph></text>"
            % "</paragraph><paragraph>".join(content_clean)
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
                print "No key defined for %s" % line
                continue
            content.append(line)
    if key:
        texts[key] = wrapup(content)
    return texts


def add_text(key, text, pstyles, cstyles):
    sc.selectText(0, 0, key)
    sc.deleteText(key)

    errors = []

    root = ET.fromstring(text)
    cursor_pos = 0
    current_style = NO_STYLE
    for p in root:
        if p.text:
            sc.insertText(p.text, -1, key)
            cursor_pos += len(p.text)

        for s in p:
            if s.tag == "t":
                if not s.text:
                    errors.append("t tags should have text")
                else:
                    sc.insertText(s.text, -1, key)
                    cursor_pos += len(s.text)

                rt_l = cursor_pos - len(s.text)
                sc.selectText(rt_l, -1, key)
                if "f" in s.attrib:
                    font_name = s.attrib["f"]
                    try:
                        sc.setFont(s.attrib["f"], key)
                    except Exception:
                        errors.append("Invalid font name: %s" % font_name)
                if "c" in s.attrib:
                    # not currently defined color name will be added with
                    # a brown color
                    # TODO but no way to tell ?
                    sc.setTextColor(s.attrib["c"], key)
                if "s" in s.attrib:
                    font_size = s.attrib["s"]
                    try:
                        sc.setFontSize(int(font_size), key)
                    except Exception:
                        errors.append("Invalid font size: %s" % font_size)
                sc.selectText(0, 0, key)  # deselect

            elif s.tag == "cs":
                if not s.text:
                    errors.append("cs tags should have text")
                else:
                    sc.insertText(s.text, -1, key)
                    cursor_pos += len(s.text)

                rt_l = cursor_pos - len(s.text)
                sc.selectText(rt_l, -1, key)
                if "n" in s.attrib:
                    char_style = s.attrib["n"]
                    sc.setCharacterStyle(char_style, key)
                else:
                    errors.append("cs tags should have a 'n' attribute")
                sc.selectText(0, 0, key)  # deselect

            elif s.tag == "ps":
                # change the state of the current style for this paragraph
                # and the following
                if "n" in p[0].attrib:
                    current_style = p[0].attrib["n"]
                    if not current_style:
                        current_style = NO_STYLE
                else:
                    errors.append("ps tags should have a 'n' attribute")
                if s.text:
                    errors.append("ps tags should not have text")

            # text as is
            if s.tail:
                sc.insertText(s.tail, -1, key)
                cursor_pos += len(s.tail)

        sc.insertText("\r", -1, key)
        cursor_pos += 1
        sc.selectText(cursor_pos - 1, -1, key)
        sc.setStyle(current_style, key)
        sc.selectText(0, 0, key)  # deselect

    sc.deselectAll()
    sc.docChanged(True)

    if errors:
        _error("Errors while processing '%s':\n- %s" % (key, "\n- ".join(errors)))


def _debug(o):
    if DEBUG:
        sc.messageBox("DEBUG", repr(o))


def _error(o, icon=sc.ICON_WARNING):
    result = sc.messageBox(
        "ERROR", o, icon, sc.BUTTON_OK | sc.BUTTON_DEFAULT, sc.BUTTON_ABORT,
    )
    if result == sc.BUTTON_ABORT:
        sys.exit(1)


def main(argv):
    if not sc.haveDoc():
        _error("Need a document", sc.ICON_CRITICAL)
        sys.exit(1)

    pstyles, cstyles = prep()
    texts = read_data(data_file)
    # _debug(texts)

    sc.setRedraw(False)

    num_selected = sc.selectionCount()
    if num_selected:
        sc.messageBox("Debug", "Selected %d" % num_selected)
        for i in range(num_selected):
            key = sc.getSelectedObject(i)
            if sc.getObjectType(key) != "TextFrame":
                _error("Selected object with name %s not a text frame" % key)
                continue
            if key not in texts:
                _error("Selected text frame with name %s not in data" % key)
                continue
    else:
        # go through the texts keys
        sc.progressTotal(len(texts))
        progress = 0
        for key, text in texts.items():
            progress += 1
            sc.progressSet(progress)
            # TODO process pages later
            if key.startswith("#"):
                continue

            # sc.messageBox("DEBUG", key)

            # TODO keep around ? and display at the end ?
            if not sc.objectExists(key):
                _error("Object %s from data not found" % key)
                continue
            if sc.getObjectType(key) != "TextFrame":
                _error("Object %s from data not a text frame" % key)
                continue

            add_text(key, texts[key], pstyles, cstyles)


def main_wrapper(argv):
    try:
        sc.statusMessage("Running script...")
        sc.progressReset()
        main(argv)
    finally:
        if sc.haveDoc():
            sc.setRedraw(True)
        sc.statusMessage("Done")
        sc.progressReset()


if __name__ == "__main__":
    main_wrapper(sys.argv)
    # texts = read_data(data_file)
    # print (repr(texts))

    # xml = '<text><paragraph><ps n="My Style" />Hello World.</paragraph><paragraph></paragraph><paragraph>Second line <t s="24">with</t> My Style</paragraph><paragraph><ps n="" />This line has no style <t f="Times New Roman" s="18" c="Red" >but has</t> char styles and <cs n="superscript">font</cs> change</paragraph></text>'
    # root = ET.fromstring(xml)
