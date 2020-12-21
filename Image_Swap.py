# -*- coding: utf-8 -*-
"""
To swap images around in a photobook (single image per page, same sizes)
Select image then run. 
In the dialog, enter the new page number for the image : the images
will be swapped.
If M prefix is used before the number: the selected image is moved to the selected
page, then the images between are moved to fill the gap
"""

import sys

from common import sc, scdebug, scerror


def try_int(string):
    try:
        return int(string)
    except Exception:
        return None


def get_swap_page(swap):
    with_page = try_int(swap)
    if with_page is None:
        scerror("Invalid page number")
        sys.exit(1)

    pc = sc.pageCount()
    if with_page < 1 or with_page > pc:
        scerror("Bad page number")
        sys.exit(1)

    return with_page


def get_image_frame():
    for item, _, _ in sc.getPageItems():
        # suppose only 1 image frame
        if sc.getObjectType(item) == "ImageFrame":
            return item
    return None


def get_page(item):
    for i in range(1, sc.pageCount() + 1):
        sc.gotoPage(i)
        for page_item, _, _ in sc.getPageItems():
            if page_item == item:
                return i
    return -1


class ImageSpec:
    def __init__(self, item, page_number, scale, offset, file_path):
        self.item = item
        self.page_number = page_number
        self.scale = scale
        self.offset = offset
        self.file_path = file_path


def get_image_on_page(page_number):
    sc.gotoPage(page_number)
    return get_image_frame()


def get_image_spec(page_number):
    sc.gotoPage(page_number)
    image_frame = get_image_frame()
    if not image_frame:
        return None

    scale = sc.getImageScale(image_frame)
    offset = sc.getImageOffset(image_frame)
    file_path = sc.getImageFile(image_frame)
    return ImageSpec(image_frame, page_number, scale, offset, file_path)


def set_image(image_spec, image_frame):
    sc.loadImage(image_spec.file_path, image_frame)
    sc.setImageScale(*(image_spec.scale + (image_frame,)))
    sc.setImageOffset(*(image_spec.offset + (image_frame,)))


def swap(image_spec_base, image_spec_swap):
    set_image(image_spec_swap, image_spec_base.item)
    set_image(image_spec_base, image_spec_swap.item)


def main(argv):
    if not sc.haveDoc():
        scerror("No document open!")
        sys.exit(1)

    nbrSelected = sc.selectionCount()
    if nbrSelected == 0:
        scerror("No item is selected !")
        sys.exit(1)

    # can be the image or some other element in the same page (like
    # the page number text)
    item = sc.getSelectedObject(0)

    # will be valid (image_item exists)
    page_number = get_page(item)
    image_spec_base = get_image_spec(page_number)
    if image_spec_base is None:
        scerror("No Image on current page")
        sys.exit(1)

    swap_command = sc.valueDialog("Swap command", "Prefix M to insert", "")

    if not swap_command:
        sys.exit(0)

    swap_command = swap_command.upper().strip()

    if swap_command[0] == "M":
        # move
        # suppose there is an image frame on all pages between the
        # current page and the chosen swap page
        swap_page_number = get_swap_page(swap_command[1:])
        if swap_page_number == page_number:
            scerror("Same page !")
            sys.exit(1)

        sc.progressReset()
        progress = 0

        if image_spec_base.page_number > swap_page_number:
            move_pages_range = range(swap_page_number, image_spec_base.page_number)
            move_image_specs = [get_image_spec(i) for i in move_pages_range]

            sc.progressTotal(len(move_pages_range))
            set_image(image_spec_base, move_image_specs[0].item)
            for i in range(len(move_image_specs) - 1):
                set_image(move_image_specs[i], move_image_specs[i + 1].item)
                progress += 1
                sc.progressSet(progress)
            set_image(move_image_specs[-1], image_spec_base.item)
        else:
            move_pages_range = range(
                image_spec_base.page_number + 1, swap_page_number + 1
            )
            move_image_specs = [get_image_spec(i) for i in move_pages_range]

            sc.progressTotal(len(move_pages_range))
            set_image(image_spec_base, move_image_specs[-1].item)
            set_image(move_image_specs[0], image_spec_base.item)
            for i in range(1, len(move_image_specs)):
                set_image(move_image_specs[i], move_image_specs[i - 1].item)
                progress += 1
                sc.progressSet(progress)

        sc.progressReset()
    else:
        # swap
        swap_page_number = get_swap_page(swap_command)
        if swap_page_number == page_number:
            scerror("Same page !")
            sys.exit(1)

        image_spec_swap = get_image_spec(swap_page_number)
        if image_spec_swap is None:
            scerror("No Image on selected swap page")
            sys.exit(1)

        swap(image_spec_base, image_spec_swap)


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
        sc.docChanged(True)


if __name__ == "__main__":
    main_wrapper(sys.argv)
