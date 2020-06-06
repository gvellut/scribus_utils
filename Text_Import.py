# -*- coding: utf-8 -*-

import os
import sys

import scribus as sc

# TODO tester linked frames

KEY_PREFIX = "#---"
COPY_PREFIX = "Copy of "

# __file__ is not defined but the dir of the script being exed is in sys.path 0
data_file = os.path.join(sys.path[0], "test_data.txt")


def prep():
    paragraph_styles = sc.getParagraphStyles()
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

    sc.insertText(text, -1, key)


def main(argv):
    if not sc.haveDoc():
        sc.messageBox("Error", "Need a document")
        return

    pstyles, cstyles = prep()
    texts = read_data(data_file)
    sc.messageBox("Debug", repr(texts))

    sc.setRedraw(False)

    num_selected = sc.selectionCount()
    if num_selected:
        sc.messageBox("Debug", "Selected %d" % num_selected)
        for i in range(num_selected):
            key = sc.getSelectedObject(i)
            if sc.getObjectType(key) != "TextFrame":
                sc.messageBox(
                    "Error", "Selected object with name %s not a text frame" % key
                )
                continue
            if key not in texts:
                sc.messageBox(
                    "Error", "Selected text frame with name %s not in data" % key
                )
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

            sc.messageBox("DEBUG", key)

            # TODO keep around ? and display at the end ?
            if not sc.objectExists(key):
                sc.messageBox("Error", "Object %s from data not found" % key)
                continue
            if sc.getObjectType(key) != "TextFrame":
                sc.messageBox("Error", "Object %s from data not a text frame" % key)
                continue

            add_text(key, texts[key], pstyles, cstyles)

    sc.docChanged(True)
    sc.statusMessage("Import done")


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

"""
obj = getSelectedObject(0)
print (obj)
selectText(0, 0, obj)
deleteText(obj)

style = "My Style"

cursorPosition = 0
print cursorPosition
firstLineText = "First Line Text"

insertText(firstLineText, -1, obj)
cursorPosition = cursorPosition + len(firstLineText)
insertText("\r", -1, obj)
cursorPosition = cursorPosition + 1

selectText(cursorPosition - 1, 1, obj)
print (repr(getText(obj)))
setStyle(style, obj)
selectText(0, 0, obj)
print ("unselect")

secondLineText = "Second Line Text"
lineStartPosition = cursorPosition
insertText(secondLineText, -1, obj)
cursorPosition = cursorPosition + len(secondLineText)
insertText("\r", -1, obj)
cursorPosition = cursorPosition + 1

selectText(cursorPosition - 1, 1, obj)
print (repr(getText(obj)))
setStyle("Default Paragraph Style", obj)

thirdLineText = "Third Line Text"
insertText(thirdLineText, -1, obj)
cursorPosition = cursorPosition + len(thirdLineText)
insertText("\r", -1, obj)
cursorPosition = cursorPosition + 1

selectText(cursorPosition - 1, 1, obj)
print (repr(getText(obj)))
setStyle(style, obj)


obj = getSelectedObject(0)
print (obj)
f = getFontFeatures()
print (f)
"""
