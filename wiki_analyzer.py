"""Given a source page on wikipedia, finds the path to the Philosophy page
"""

import requests
from bs4 import BeautifulSoup
import re
from collections import defaultdict
from multiprocessing import Pool
from tabulate import tabulate
from operator import itemgetter
import argparse
import sys

from errors import *

INFINITY = 1000
URL_REGEX = re.compile(r'https?://(.*\.)*wikipedia.org/wiki/([a-zA-Z0-9\(\)_:]+)#?')
_SPECIAL_RANDOM = 'Special:Random'


def is_valid_path(link):
    """Checks whether this link is the first non-italicized, non-parenthesized link in the body of the article"""
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
    if count != 0:
        return False
    return True


def get_leaf(link):
    m = URL_REGEX.match(link)
    if not m or not m.groups():
        raise BadLinkException(link)
    groups = m.groups()
    if len(groups) < 2:
        raise BadLinkException(link)
    return groups[1]


DEFAULT_LINK_PREDICATES = [is_valid_path]

class WikiAnalyzer(object):
    """Given a source page and a destination page, find path between them"""
    cache = {}
    def __init__(self, source, dest, *link_predicates):
        self.source = source
        self.dest = dest
        self.link_predicates = link_predicates
        if not self.link_predicates:
            self.link_predicates = DEFAULT_LINK_PREDICATES

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
        dest_leaf = get_leaf(dest)
        if source_leaf in WikiAnalyzer.cache and source_leaf != _SPECIAL_RANDOM:
            return WikiAnalyzer.cache[source_leaf]
        path_len = 0
        current = source
        path = []
        seen = set()

        while path_len < INFINITY:
            leaf = get_leaf(current)
            if dest_leaf == leaf:
                return path

            if leaf != _SPECIAL_RANDOM and leaf in seen:
                raise RouteLoopException(current)

            if leaf != _SPECIAL_RANDOM and leaf in WikiAnalyzer.cache:
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
                if all(p(link) for p in self.link_predicates):
                    current = link.attrs.get('href')
                    if current.startswith('//'):
                        current = 'http:' + current
                    if current.startswith('http') and 'wikipedia.org' not in current:
                        continue
                    if not current.startswith('http'):
                        current = 'http://wikipedia.org' + current
                    if current.startswith('https://'):
                        current = current.replace('https://', 'http://')
                    path_len += 1
                    break
            else:
                raise NoRouteException(current)
        
        # Backtrack and cache partial paths
        WikiAnalyzer._cache_intermediate_paths(path)
        return path


def _analyze_paths_to_philosophy(args):
        """Computes paths to 'num' random pages and returns the distribution"""
        counts = defaultdict(int)
        seed = 'http://wikipedia.org/wiki/Special:Random'
        dest, num = args[0], args[1]
        for i in xrange(num):
            try:
                w = WikiAnalyzer(seed, dest)
                path = w.path
                counts[len(path)] += 1
            except (BadPageException, BadLinkException, RouteLoopException, NoRouteException) as ex:
                counts[INFINITY] += 1
        return counts


def analyze_paths_to_dest(dest='http://wikipedia.org/wiki/Philosophy'):
    """ Analyzes a sample of 500 random wikipedia pages and computes distribution of path lengths """
    counter = defaultdict(int)
    pool = Pool(20)
    counts = pool.map(_analyze_paths_to_philosophy, [(dest, 25)] * 20)
    for c in counts:
        for path_len, count in c.iteritems():
            counter[path_len] += count
    return counter


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source", help="http link to the starting wikipedia document")
    parser.add_argument("-d", "--dest", help="http link to the ending wikipedia document. Computes distribution if no source provided.")
    args = parser.parse_args()
    if args.source and args.dest:
        w = WikiAnalyzer(args.source, args.dest)
        print "Path from source to destination: "
        print w.path
        exit(0)
    else:
        dest = args.dest or 'http://wikipedia.org/wiki/Philosophy'
        print "Analyzing paths to: ", dest, " ..."
        counts = analyze_paths_to_dest(dest)
        table = [('Path Length', 'Count')] + sorted(counts.items(), key=itemgetter(0))
        sum = 0
        for pathlen, count in counts.iteritems():
            sum += count
            if sum >= 250:
                print "Median path length: ", pathlen
                break
        print "Percentage of pages which lead to philosophy: ", float(500 - counts.get(INFINITY, 0)) / 500 * 100, "%"
        print tabulate(table)
