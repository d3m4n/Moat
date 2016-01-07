import requests
from bs4 import BeautifulSoup

INFINITY = 1000
class BadPageException(Exception):
    pass

class RouteLoopException(Exception):
    pass

class NoRouteException(Exception):
    pass

class WikiAnalyzer(object):
    cache = {}

    def __init__(self, source, dest, *args, **kwargs):
        self.source = source
        self.dest = dest

    def _is_valid_path(self, link):
        if not link.parent:
            return False
        if not link.attrs or not link.attrs.get('href'):
            return False

        if link.parent.name != 'p':
            return False

        if link.parent.attrs and 'hatnote' in link.parent.attrs.get('class', []):
            return False

        if link.attrs and 'image' in link.attrs.get('class', []):
            return False

        idx = link.parent.text.find(link.text)
        count = 0
        for i, c in enumerate(link.parent.text):
            if i >= idx:
                break
            if c == '(':
                count += 1
            elif c == ')':
                count -= 1
        if count == 1:
            return False
        return True

    @property
    def route(self):
        source, dest = self.source, self.dest
        if source in WikiAnalyzer.cache:
            return WikiAnalyzer.cache[source]
        route_len = 0
        current = source
        path = []
        seen = set()
        while dest not in current and route_len < INFINITY:
            if current in seen:
                raise RouteLoopException(current)

            if current in WikiAnalyzer.cache:
                WikiAnalyzer.cache[source] = path + WikiAnalyzer.cache[current]
                return WikiAnalyzer.cache[source]

            r = requests.get(current)
            if not r:
                raise BadPageException(source)

            parser = BeautifulSoup(r.text, 'lxml')
            seen.add(current)
            path.append(current)
            div = parser.find('div', {'id': 'mw-content-text'})
            links = div.findAll('a')
            for link in links:
                if self._is_valid_path(link):
                    current = link.attrs.get('href')
                    if not current.startswith('http://wikipedia.org'):
                        current = 'http://wikipedia.org' + current
                    route_len += 1
                    break
            else:
                raise NoRouteException(current)

        for i, n in enumerate(path):
            WikiAnalyzer.cache[n] = path[i:]
        return path


