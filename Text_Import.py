# -*- coding: utf-8 -*-

import codecs
import os
import re
import sys
import xml.etree.ElementTree as ET

from common import sc, scdebug, scerror

# TODO tester linked frames

KEY_PREFIX = "#---"
NO_STYLE = "Default Paragraph Style"

# spaces : snb sen sem stn stk  smi sha
# dashes : dem den
ENTITIES = {
    "snb": u"\u00A0",  # non breaking
    "sen": u"\u2002",  # en space
    "sem": u"\u2003",  # em space
    "stn": u"\u2009",  # thin
    "stu": u"\u202F",  # unbreakable thin
    "stk": u"\u2004",  # thick 1/3
    "smi": u"\u2005",  # mid 1/4
    "sha": u"\u200A",  # hair
    "znb": u"\uFEFF",  # zero width no break
    "shy": u"\u00AD",  # soft hyphen
    "dem": u"\u2014",  # em dash
    "den": u"\u2013",  # en dash
}
XML_ENTITIES = set(["lt", "gt", "amp", "quot"])

KEY_SEP_SUFFIX = "---sep"
LINE_SEP = "###"

# __file__ is not defined when running from Scribus but the dir of
# the script being executed is in sys.path 0
# data_file = os.path.join(sys.path[0], "test_data.txt")
# data_file = sc.fileDialog("Data file", issave=True)
# **** CHANGE ****
data_file = (
    "/Users/guilhem/Documents/projects/github/hikingprintmap/___jp/data_text.txt"
)


def prep():
    paragraph_styles = set(sc.getParagraphStyles())
    char_styles = set(sc.getCharStyles())
    return paragraph_styles, char_styles


def read_data(data_file):
    with codecs.open(data_file, encoding="utf-8") as f:
        data = f.read()

    def wrapup(content, is_sep):
        # remove empty lines at the beginning and end
        content_clean = []
        for i, c in enumerate(content):
            if len(c.strip()) != 0:
                content_clean = content[i:]
                break
        for i, c in enumerate(reversed(content_clean)):
            if len(c.strip()) != 0:
                content_clean = content_clean[: len(content_clean) - i]
                break
        if is_sep:
            content_clean = "".join(content_clean)
            content_clean = content_clean.split(LINE_SEP)
        return (
            u"<text>\n<paragraph>%s</paragraph>\n</text>"
            % u"</paragraph>\n<paragraph>".join(content_clean)
        )

    lines = data.splitlines()
    texts = {}
    key = None
    content = None
    is_sep = False
    for line in lines:
        if line.startswith(KEY_PREFIX):
            if key:
                texts[key] = wrapup(content, is_sep)
            key = line[len(KEY_PREFIX) :].strip()
            if key.endswith(KEY_SEP_SUFFIX):
                is_sep = True
                key = key[: -len(KEY_SEP_SUFFIX)]
            else:
                is_sep = False
            content = []
        else:
            if not key:
                print u"No key defined for %s" % line
                continue
            content.append(line)
    if key:
        texts[key] = wrapup(content, is_sep)
    return texts


def add_text(key, text, pstyles, cstyles):
    sc.selectText(0, 0, key)
    sc.deleteText(key)

    errors = []

    text_ent = _process_entities(text)
    try:
        root = ET.fromstring(text_ent.encode("utf-8"))
    except ET.ParseError as ex:
        iline, icolumn = ex.position
        # 1-based
        iline -= 1
        icolumn -= 1
        lines = text_ent.splitlines()
        line = lines[iline]
        imin = max(0, icolumn - 60)
        imax = min(len(line), icolumn + 61)
        # TODO remove tags added by read_data not in original text ?
        # cn be confusing if tag missing not found at the end
        # like tags <paragraph>
        subtext = "%s__(%s)__%s" % (
            line[imin:icolumn],
            line[icolumn],
            line[icolumn + 1 : imax],
        )
        scerror(u"Error around '%s'" % subtext)
        sys.exit(1)

    cursor_pos = 0
    current_style = NO_STYLE
    for p in root:
        if p.text:
            sc.insertText(p.text, -1, key)
            cursor_pos += len(p.text)

        cchanges = []
        for s in p:
            if s.tag == "t":
                if not s.text:
                    errors.append(u"t tags should have text")
                else:
                    t = s.text

                    # do it first since can change text content and length
                    if "z" in s.attrib:
                        modified_text = []
                        # If soft hyphen => prevent insertion of znb so the Japanese
                        # text gets cut in new lines ; remove them (because would cause
                        # soft hyphen dash to be inserted) and insert znb between other
                        # letters
                        start_text_pos = 0
                        for i, c in enumerate(t):
                            # soft hyphen
                            if c == ENTITIES["shy"]:
                                if i != start_text_pos:
                                    ls = start_text_pos
                                    rs = ls + i - start_text_pos
                                    modified_text.extend(ENTITIES["znb"].join(t[ls:rs]))
                                # exclude soft hyphen
                                start_text_pos = i + 1

                        if start_text_pos != len(t):
                            ls = start_text_pos
                            rs = ls + len(t) - start_text_pos
                            modified_text.extend(ENTITIES["znb"].join(t[ls:rs]))

                        t = "".join(modified_text)

                    sc.insertText(t, -1, key)
                    char_range = (cursor_pos, len(t))
                    cursor_pos += len(t)

                    if "f" in s.attrib:
                        font_name = s.attrib["f"]
                        try:
                            cchanges.append(
                                (char_range, sc.setFont, s.attrib["f"], key)
                            )
                        except Exception:
                            errors.append(u"Invalid font name: %s" % font_name)
                    if "c" in s.attrib:
                        # not currently defined color name will be added with
                        # a brown color
                        # TODO but no way to tell ?
                        color = s.attrib["c"]
                        cchanges.append((char_range, sc.setTextColor, color, key))
                    if "s" in s.attrib:
                        font_size = s.attrib["s"]
                        try:
                            cchanges.append(
                                (char_range, sc.setFontSize, int(font_size), key)
                            )
                        except Exception:
                            errors.append(u"Invalid font size: %s" % font_size)
            elif s.tag == "cs":
                if not s.text:
                    errors.append(u"cs tags should have text")
                else:
                    t = s.text
                    sc.insertText(t, -1, key)
                    cursor_pos += len(t)

                    rt_l = cursor_pos - len(t)
                    char_range = (rt_l, len(t))
                    if "n" in s.attrib:
                        # TODO check if in current styles ?
                        char_style = s.attrib["n"]
                        cchanges.append(
                            (char_range, sc.setCharacterStyle, char_style, key)
                        )
                    else:
                        errors.append(u"cs tags should have a 'n' attribute")

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

        for cchange in cchanges:
            char_range, change = cchange[0], cchange[1:]
            sc.selectText(char_range[0], char_range[1], key)
            change[0](*change[1:])
            sc.selectText(0, 0, key)

    if errors:
        scerror(u"Errors while processing '%s':\n- %s" % (key, "\n- ".join(errors)))


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


def main(argv):
    if not sc.haveDoc():
        scerror(u"Need a document", sc.ICON_CRITICAL)
        sys.exit(1)

    pstyles, cstyles = prep()
    texts = read_data(data_file)
    # scdebug(texts)

    sc.setRedraw(False)

    num_selected = sc.selectionCount()
    if num_selected:
        # first, copy the list of selected objects (later processing will
        # change that list => issues if used directly)
        keyList = []
        for i in range(num_selected):
            keyList.append(sc.getSelectedObject(i))

        sc.progressTotal(len(keyList))

        for i in range(num_selected):
            sc.progressSet(i + 1)

            key = keyList[i]
            if sc.getObjectType(key) != "TextFrame":
                scerror(u"Selected object with name '%s' not a text frame" % key)
                continue
            if key not in texts:
                scerror(u"Selected text frame with name '%s' not in data" % key)
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

                # TODO keep around ? and display at the end ?
                if not sc.objectExists(key):
                    scerror(u"Object %s from data not found" % key)
                    continue
                if sc.getObjectType(key) != "TextFrame":
                    scerror(u"Object %s from data not a text frame" % key)
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
