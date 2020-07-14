# -*- coding: utf-8 -*-
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

from common import sc, scdebug, scerror


def get_image_x(position, default=0.0):
    imageX = default
    if position == "L":
        imageX = 0.0
    elif position == "C":
        imageX = (frameW - imageW) / 2.0
    elif position == "R":
        imageX = frameW - imageW
    return imageX


def get_image_y(position, default=0.0):
    imageY = default
    if position == "T":
        imageY = 0.0
    elif position == "M":
        imageY = (frameH - imageH) / 2.0
    elif position == "B":
        imageY = frameH - imageH
    return imageY


if not sc.haveDoc():
    scerror("No document open!")
    sys.exit(1)

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

if not position:
    sys.exit(0)

position = position.upper()
objList = []
for i in range(nbrSelected):
    objList.append(sc.getSelectedObject(i))

for i in range(nbrSelected):
    obj = objList[i]
    if sc.getObjectType(obj) != "ImageFrame":
        # TODO warning dialog ?
        continue
    imageX, imageY = sc.getImageOffset(obj)
    frameW, frameH = sc.getSize(obj)
    saveScaleX, saveScaleY = sc.getImageScale(obj)
    sc.setScaleImageToFrame(1, 0, obj)
    fullScaleX, fullScaleY = sc.getImageScale(obj)
    sc.setScaleImageToFrame(0, 0, obj)
    sc.setImageScale(saveScaleX, saveScaleY, obj)
    imageW = frameW * (saveScaleX / fullScaleX)
    imageH = frameH * (saveScaleY / fullScaleY)

    if len(position) == 1:
        position = position[0]
        imageX = get_image_x(position, default=imageX)
        imageY = get_image_y(position, default=imageY)
    else:
        imageX = get_image_x(position[1], default=imageX)
        imageY = get_image_y(position[0], default=imageY)

    sc.setImageOffset(imageX, imageY, obj)
    sc.docChanged(1)
    sc.setRedraw(True)
sc.setUnit(restore_units)

if sc.haveDoc():
    sc.redrawAll()
