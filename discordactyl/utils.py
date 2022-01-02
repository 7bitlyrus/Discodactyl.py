import logging


# Modified from https://stackoverflow.com/a/55708449
async def quit_on_exception(awaitable):
    try:
        return await awaitable
    except Exception:
        logging.exception("Unhandled exception")
        quit()


# https://docs.python.org/3/howto/logging-cookbook.html#using-loggeradapters-to-impart-contextual-information
class CustomAdapter(logging.LoggerAdapter):
    """
    This example adapter expects the passed in dict-like object to have a
    'connid' key, whose value in brackets is prepended to the log message.
    """

    def process(self, msg, kwargs):
        return '[%s] %s' % (self.extra['connid'], msg), kwargs


# Modified from https://github.com/litl/backoff/blob/master/README.rst
def fatal_http_code(e):
    try:
        return 400 <= e.response.status_code < 500
    except:
        return False
