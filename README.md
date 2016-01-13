## Paths to Philosophy Analyzes wikipedia pages following the first
link in the body of the page which is not parenthesized and
italisized. This process continues till the Philosophy page is reached
(http://wikipedia.org/Philosophy). The code applies a large number of
heuristics to identify "first link in the body" of the page. These
heuristics are configurable and can be replaced by another list of
predicates.

## Path Distribution and Statistics
Based on repeated analysis, the median path length to Philosophy is
14. The code computes a distribution of paths if run without any
arguments. A distribution from one run of the code is included in
distribution.txt. Roughly 92-94% of the pages reach the Philosophy
page based on experiments run.


## Design Decisions
While computing the path to philosophy, the code backtracks and caches
the intermediate paths to philosophy as well (Note: This could have
been done in one loop, but I kept it in a separate backtracking loop
because the path lengths are usually very small and this keeps the
logic simple and more readable). By caching and computing intermediate
paths, we avoid making unnecessary http requests.

For parsing the wikipedia pages themselves, PyQuery is used. lxml with
xpath would have been slightly faster, but PyQuery is more readable in
my opinion. It is also much faster than traditional choices like
BeautifulSoup. Scrapy would have been another option but it seemed
like overkill for a small task like this.