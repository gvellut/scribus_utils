from scribus import *

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
