import pytest

from ..wiki_analyzer import WikiAnalyzer, get_leaf
from ..errors import *

DEST = 'http://wikipedia.org/wiki/Philosophy'


def test_basic():
    """ Straightforward test """
    src = 'https://en.wikipedia.org/wiki/Art'
    w = WikiAnalyzer(src, DEST)
    assert (['Art', 'Human_behavior', 'Motion_(physics)',
            'Physics', 'Natural_science', 'Science',
            'Knowledge', 'Awareness',
            'Conscious', 'Quality_(philosophy)'] == w.path)


def test_dest():
    """ Test with src == dest """
    src = 'https://en.wikipedia.org/wiki/Philosophy'
    w = WikiAnalyzer(src, DEST)
    assert [] == w.path


def test_stress():
    """ Test a page with a large number of links and a strange structure """
    src = 'https://en.wikipedia.org/wiki/Star_Wars'
    w = WikiAnalyzer(src, DEST)
    assert (['Star_Wars', 'Epic_film', 'Genre',
             'Literature', 'Culture',
             'Edward_Burnett_Tylor',
             'Anthropologist',
             'Knowledge',
             'Awareness',
             'Conscious',
             'Quality_(philosophy)'] == w.path)


def test_parenthesis():
    """ Test a page with nested parenthesis """
    src = 'https://en.wikipedia.org/wiki/Genre'
    w = WikiAnalyzer(src, DEST)
    assert 'Literature' == w.path[1]


def test_leafs():
    link1 = 'http://wikipedia.org/wiki/Art'
    link2 = 'https://www.wikipedia.org/wiki/Art'
    link3 = 'http://wikipedia.org/wiki/Art#tag'
    link4 = 'https://something.somethingelse.wikipedia.org/wiki/Art'
    
    assert all(get_leaf(l) == 'Art' for l in [link1, link2, link3, link4])
    
    link5 = 'http://google.com'
    with pytest.raises(BadLinkException):
        get_leaf(link5)
