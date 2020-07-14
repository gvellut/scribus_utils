# -*- coding: utf-8 -*-
import codecs
import errno
from HTMLParser import HTMLParser
import os
import shutil
import sys

from common import sc

root_dir = ""  # sys.argv[1]
if not root_dir:
    try:
        # must run inside Scribus
        # root_dir is the path of current document
        root_dir = os.path.dirname(sc.getDocName())
    except Exception:
        print (
            "Root Dir is None and script is not running in Scribus or with no open "
            "doc. Edit the script and change it"
        )
        sys.exit(1)
else:
    # don't care about current document
    sc = None

is_remove = True
trash_name = "__cleanup"

# make absolute so all paths from os.walk are absolute
root_dir = os.path.abspath(root_dir)

trash_dir = os.path.join(root_dir, trash_name)


def _get_files_with_ext(root_dir, *exts):
    files_with_ext = []
    # subdir is absolute if root_dir is abs
    for subdir, dirs, files in os.walk(root_dir, topdown=True):
        if subdir.startswith(trash_dir):
            del dirs[:]
            continue
        for file_ in files:
            _, fext = os.path.splitext(file_)
            if fext in exts:
                files_with_ext.append(os.path.join(subdir, file_))
    return files_with_ext


class ImgObjetctParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.img_paths = []

    def handle_starttag(self, tag, tag_attrs):
        if tag.upper() != "PAGEOBJECT":
            return

        is_img = False
        for tag_attr in tag_attrs:
            if tag_attr[0].upper() == "PTYPE":
                # image
                is_img = tag_attr[1] == "2"

        if is_img:
            for tag_attr in tag_attrs:
                if tag_attr[0].upper() == "PFILE":
                    self.img_paths.append(tag_attr[1])


def _img_paths(sla_path):
    with codecs.open(sla_path, "r", "utf-8") as f:
        content = f.read()
    parser = ImgObjetctParser()
    parser.feed(content)
    sla_dir = os.path.dirname(sla_path)
    return map(lambda x: os.path.join(sla_dir, x), parser.img_paths)


def _mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python ≥ 2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


slas = _get_files_with_ext(root_dir, ".sla")
sla_imgs = []
for sla in slas:
    sla_imgs.extend(_img_paths(sla))

# this tool will only deal with images below the root dir
images = set(_get_files_with_ext(root_dir, ".jpeg", ".jpg", ".png"))

imgs_found = len(images)
images.difference_update(sla_imgs)


info_msg = (
    "%d images found in SLA\n%d images found in tree below ROOT DIR\n"
    "%d images to delete in tree\n%d images kept in tree\nwill delete=%r"
) % (len(sla_imgs), imgs_found, len(images), imgs_found - len(images), is_remove,)

if not sc:
    print info_msg
else:
    result = sc.messageBox(
        "INFO",
        info_msg,
        sc.ICON_INFORMATION,
        sc.BUTTON_OK | sc.BUTTON_DEFAULT,
        sc.BUTTON_ABORT,
    )
    if result == sc.BUTTON_ABORT:
        sys.exit(1)

_mkdir_p(trash_dir)
for image_path in images:
    rel_path = os.path.relpath(image_path, root_dir)
    new_path = os.path.join(trash_dir, rel_path)
    new_filetree = os.path.dirname(new_path)
    _mkdir_p(new_filetree)
    shutil.copy2(image_path, new_path)
    if is_remove:
        try:
            os.remove(image_path)
        except Exception as ex:
            print "There was an error removing %r" % image_path
