# This script scales the image so that it fills the frame completely.
# One dimension of the image (width/height) may overflow the frame,
# but at least one dimension will fill the frame exactly.

# License
# Copyright 2007, Jeremy Brown (TrnsltLife)
# This script is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.

from scribus import *

if haveDoc():
    nbrSelected = selectionCount()

objList = []

for i in range(nbrSelected):
    objList.append(getSelectedObject(i))

for i in range(nbrSelected):
    try:
        obj = objList[i]
        setScaleImageToFrame(True, False, obj)
        scaleX, scaleY = getImageScale(obj)
        setScaleImageToFrame(False, False, obj)
        if scaleX > scaleY:
            scale = scaleX
            setImageScale(scale, scale, obj)
        elif scaleY > scaleX:
            scale = scaleY
            setImageScale(scale, scale, obj)
        docChanged(1)
        setRedraw(True)
    except:
        nothing = "nothing"
