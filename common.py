import sys

DEBUG = True

try:
    import scribus as sc
except Exception:

    class ScribusProxy(object):
        def __getattr__(self, name):
            if name == "messageBox":

                def _messageBox(*args, **kwargs):
                    print("MessageBox %s" % args[1])

                return _messageBox

            def _missing(*args, **kwargs):
                print("%s * %r ** %r" % (name, args, kwargs))

            return _missing

    sc = ScribusProxy()


def scdialog(text, title, icon=sc.ICON_INFORMATION):
    result = sc.messageBox(
        title, text, icon, sc.BUTTON_OK | sc.BUTTON_DEFAULT, sc.BUTTON_ABORT
    )
    if result == sc.BUTTON_ABORT:
        sys.exit(1)


def scdebug(o, icon=sc.ICON_INFORMATION):
    if DEBUG:
        scdialog(repr(o), "DEBUG", icon)


def scerror(text, icon=sc.ICON_WARNING):
    scdialog(text, "ERROR", icon)
