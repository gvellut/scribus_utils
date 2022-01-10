import os
import re
import sys

from common import sc, scerror


class ImageSpec:
    def __init__(self, item, scale, offset, file_path):
        self.item = item
        self.scale = scale
        self.offset = offset
        self.file_path = file_path


def create_image_spec(image_frame):
    scale = sc.getImageScale(image_frame)
    offset = sc.getImageOffset(image_frame)
    file_path = sc.getImageFile(image_frame)
    return ImageSpec(image_frame, scale, offset, file_path)


def get_image_frames(page_number):
    return sc.getAllObjects(sc.ITEMTYPE_IMAGEFRAME, page_number)


def set_image_path(image_spec, path):
    sc.loadImage(path, image_spec.item)
    sc.setImageScale(*image_spec.scale, image_spec.item)
    sc.setImageOffset(*image_spec.offset, image_spec.item)


def swap_suffix(image_spec, suffix_swap, is_remove):
    path_base, ext = os.path.splitext(image_spec.file_path)
    if is_remove:
        if not path_base.endswith(suffix_swap):
            return
        path_base_rm = re.sub(f"{suffix_swap}$", "", path_base)
        path = f"{path_base_rm}{ext}"
    else:
        if path_base.endswith(suffix_swap):
            # already swapped probably
            return
        path = f"{path_base}{suffix_swap}{ext}"

    if not os.path.exists(path):
        # keep as is
        return
    set_image_path(image_spec, path)


def main(argv):
    if not sc.haveDoc():
        scerror("No document open!")
        sys.exit(1)

    suffix_swap = sc.valueDialog("Suffix", "Suffix", "_bw")
    if not suffix_swap:
        scerror("Empty suffix!")
        sys.exit(1)

    is_remove = False
    if suffix_swap[0] == "!":
        is_remove = True
        suffix_swap = suffix_swap[1:]

        if not suffix_swap:
            scerror("Empty suffix!")
            sys.exit(1)

    nbrSelected = sc.selectionCount()
    if nbrSelected != 0:
        selected = []
        for i in range(nbrSelected):
            selected.append(sc.getSelectedObject(i))

        for item in selected:
            # must be an image
            if sc.getObjectType(item) != "ImageFrame":
                scerror("Selection is not an image frame!")
                continue

            image_spec = create_image_spec(item)
            swap_suffix(image_spec, suffix_swap, is_remove)
    else:
        page_count = sc.pageCount()
        for i in range(page_count):
            items = get_image_frames(i)
            if not items:
                continue

            for item in items:
                image_spec = create_image_spec(item)
                swap_suffix(image_spec, suffix_swap, is_remove)


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
        sc.docChanged(True)


if __name__ == "__main__":
    main_wrapper(sys.argv)
