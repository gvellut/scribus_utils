"""
Taken from https://wiki.sc.net/canvas/Align_an_Image_in_its_Frame
No TkInter

This script will align an image inside a frame to one of 9 possible positions:
Top left, top center, top right; middle left, middle center, middle right;
or bottom left, bottom center, bottom right.

USAGE
Select one or more image frames. Run the script, which asks for your alignment
choice. Possible legitimate entries are:
TL	T	TR
L	C	R
BL	B	BR
and lowercase entries are also legitimate.

Note
There is minimal error checking, in particular no checking for frame type.
"""

import sys

import scribus as sc

if sc.haveDoc():
    restore_units = sc.getUnit()
    # since there is an issue with units other than points,
    # we switch to points then restore later.
    sc.setUnit(0)
    nbrSelected = sc.selectionCount()
    if nbrSelected == 0:
        sc.messageBox("Error:", "No frame selected")
        sys.exit(1)
    position = sc.valueDialog(
        "Image Position",
        "     T = Top,     M = Middle,     B = Bottom     \n     L = Left,     C = Center,     R = Right     \n     Example: BL = Bottom Left",
        "C",
    )
    position = position.upper()
    objList = []
    for i in range(nbrSelected):
        objList.append(sc.getSelectedObject(i))
        for i in range(nbrSelected):
            try:
                obj = objList[i]
                frameW, frameH = sc.getSize(obj)
                saveScaleX, saveScaleY = sc.getImageScale(obj)
                sc.setScaleImageToFrame(1, 0, obj)
                fullScaleX, fullScaleY = sc.getImageScale(obj)
                sc.setScaleImageToFrame(0, 0, obj)
                sc.setImageScale(saveScaleX, saveScaleY, obj)
                imageW = frameW * (saveScaleX / fullScaleX)
                imageH = frameH * (saveScaleY / fullScaleY)
                imageX = 0.0
                imageY = 0.0

                if len(position) == 1:
                    if position in ("L", "C", "R"):
                        position = "M" + position
                    elif position in ("T", "B"):
                        position += "C"

                if position[0] == "T":
                    imageY = 0.0
                elif position[0] == "M":
                    imageY = (frameH - imageH) / 2.0
                elif position[0] == "B":
                    imageY = frameH - imageH

                if position[1] == "L":
                    imageX = 0.0
                elif position[1] == "C":
                    imageX = (frameW - imageW) / 2.0
                elif position[1] == "R":
                    imageX = frameW - imageW

                sc.setImageOffset(imageX, imageY, obj)
                sc.docChanged(1)
                sc.setRedraw(True)
            except Exception:
                nothing = "nothing"
    sc.setUnit(restore_units)
else:
    sc.messageBox("Error", "No document open")
    sys.exit(1)

if sc.haveDoc():
    sc.redrawAll()
