# This script scales the image so that it fills the frame completely.
# One dimension of the image (width/height) may overflow the frame,
# but at least one dimension will fill the frame exactly.

# License
# Copyright 2007, Jeremy Brown (TrnsltLife)
# This script is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.

import scribus as sc

if sc.haveDoc():
    nbrSelected = sc.selectionCount()

objList = []

for i in range(nbrSelected):
    objList.append(sc.getSelectedObject(i))

for i in range(nbrSelected):
    try:
        obj = objList[i]
        sc.setScaleImageToFrame(True, False, obj)
        scaleX, scaleY = sc.getImageScale(obj)
        sc.setScaleImageToFrame(False, False, obj)
        if scaleX > scaleY:
            scale = scaleX
            sc.setImageScale(scale, scale, obj)
        elif scaleY > scaleX:
            scale = scaleY
            sc.setImageScale(scale, scale, obj)
        sc.docChanged(1)
        sc.setRedraw(True)
    except Exception:
        nothing = "nothing"
