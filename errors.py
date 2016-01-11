class BadPageException(Exception):
    """Raised when unable to read the contents of HTML page"""
    pass


class BadLinkException(Exception):
    """Raised when link is incorrectly formatted"""
    pass


class RouteLoopException(Exception):
    """Raised when a loop is detected trying to find the philosophy page"""
    pass


class NoRouteException(Exception):
    """Raised when reached a depth limit when trying to find philosophy page"""
    pass
