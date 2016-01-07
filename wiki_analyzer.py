"""Given a source page on wikipedia, finds the path to the Philosophy page
"""

import requests
from bs4 import BeautifulSoup
import re

INFINITY = 1000
URL_REGEX = re.compile(r'https?://(.*\.)*wikipedia.org/wiki/([a-zA-Z0-9\(\)_:]+)#?')
_SPECIAL_RANDOM = 'Special:Random'

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

def is_valid_path(link):
    if not link.parent:
        return False

    if not link.attrs or not link.attrs.get('href'):
        return False

    if link.parent.name != 'p':
        return False

    if link.parent.attrs and 'hatnote' in link.parent.attrs.get('class', []):
        return False

    if link.parent.name == 'i':
        return False

    if link.attrs and 'image' in link.attrs.get('class', []):
        return False

    if link.findParent('table', attrs={'class': 'infobox'}):
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

def get_leaf(link):
    m = URL_REGEX.match(link)
    if not m.groups():
        raise BadLinkException(link)
    groups = m.groups()
    if len(groups) < 2:
        raise BadLinkException(link)
    return groups[1]


class WikiAnalyzer(object):
    """Given a source page and a destination page, find path between them"""
    cache = {}

    def __init__(self, source, dest):
        self.source = source
        self.dest = dest
    
    @classmethod
    def _cache_intermediate_paths(cls, path):
        for i, n in enumerate(path):
            if n == _SPECIAL_RANDOM:
                continue
            cls.cache[n] = path[i:]

    @property
    def path(self):
        """Returns path from source to dest"""
        source, dest = self.source, self.dest
        source_leaf = get_leaf(source)
        if source_leaf in WikiAnalyzer.cache and source_leaf != _SPECIAL_RANDOM:
            return WikiAnalyzer.cache[source_leaf]
        path_len = 0
        current = source
        path = []
        seen = set()

        while dest not in current and path_len < INFINITY:
            leaf = get_leaf(current)

            if leaf in seen and leaf != _SPECIAL_RANDOM:
                raise RouteLoopException(current)

            if leaf in WikiAnalyzer.cache and leaf != _SPECIAL_RANDOM:
                WikiAnalyzer.cache[source_leaf] = path + WikiAnalyzer.cache[leaf]
                return WikiAnalyzer.cache[source_leaf]

            r = requests.get(current)
            if not r:
                raise BadPageException(current)

            parser = BeautifulSoup(r.text, 'lxml')

            if leaf != _SPECIAL_RANDOM:
                seen.add(leaf)
            path.append(leaf)

            div = parser.find('div', {'id': 'mw-content-text'})
            links = div.findAll('a')
            for link in links:
                if is_valid_path(link):
                    current = link.attrs.get('href')
                    if current.startswith('//'):
                        current = 'https:' + current
                    if current.startswith('http') and 'wikipedia.org' not in current:
                        continue
                    if not current.startswith('http'):
                        current = 'https://wikipedia.org' + current
                    path_len += 1
                    break
            else:
                raise NoRouteException(current)

        WikiAnalyzer._cache_intermediate_paths(path)
        return path

if __name__ == '__main__':
    dest = 'wikipedia.org/wiki/Philosophy'
    w = WikiAnalyzer('https://en.wikipedia.org/wiki/Special:Random', dest)
    print w.path
    w = WikiAnalyzer('https://en.wikipedia.org/wiki/Knowledge', dest)
    print w.path
