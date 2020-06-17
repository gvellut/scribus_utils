# -*- coding: utf-8 -*-
import sys

DEBUG = True

try:
    import scribus as sc
except Exception:

    class ScribusProxy(object):
        def __getattr__(self, name):
            if name == "messageBox":

                def _messageBox(*args, **kwargs):
                    print "MessageBox %s" % args[1]

                return _messageBox

            def _missing(*args, **kwargs):
                print "%s * %r ** %r" % (name, args, kwargs)

            return _missing

    sc = ScribusProxy()


def scdebug(o, icon=sc.ICON_INFORMATION):
    if DEBUG:
        result = sc.messageBox(
            "DEBUG", repr(o), icon, sc.BUTTON_OK | sc.BUTTON_DEFAULT, sc.BUTTON_ABORT
        )
        if result == sc.BUTTON_ABORT:
            sys.exit(1)


def scerror(o, icon=sc.ICON_WARNING):
    result = sc.messageBox(
        "ERROR", o, icon, sc.BUTTON_OK | sc.BUTTON_DEFAULT, sc.BUTTON_ABORT,
    )
    if result == sc.BUTTON_ABORT:
        sys.exit(1)
