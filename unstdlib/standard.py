from itertools import groupby, chain

import sys
import random
import string
import datetime
from collections import defaultdict


__all__ = [
    'random_string', 'get_many', 'pop_many',
    'groupby_count', 'groupby_dict',
    'iterate_date', 'iterate_chunks', 'iterate_flatten', 'iterate_date_values',
    'convert_exception',
    'number_to_string', 'string_to_number',
    'isoformat_as_datetime', 'truncate_datetime',
    'to_str', 'to_unicode',
]


def random_string(length=6, alphabet=string.letters+string.digits):
    """
    Return a random string of given length and alphabet.

    Default alphabet is url-friendly (base62).
    """
    return ''.join([random.choice(alphabet) for i in xrange(length)])


def get_many(d, required=[], optional=[], one_of=[]):
    """
    Returns a predictable number of elements out of ``d`` in a list for auto-expanding.

    Keys in ``required`` will raise KeyError if not found in ``d``.
    Keys in ``optional`` will return None if not found in ``d``.
    Keys in ``one_of`` will raise KeyError if none exist, otherwise return the first in ``d``.

    Example::

        uid, action, limit, offset = get_many(request.params, required=['uid', 'action'], optional=['limit', 'offset'])

    Note: This function has been added to the webhelpers package.
    """
    d = d or {}
    r = [d[k] for k in required]
    r += [d.get(k)for k in optional]

    if one_of:
        for k in (k for k in one_of if k in d):
            return r + [d[k]]

        raise KeyError("Missing a one_of value.")

    return r


def pop_many(d, keys, default=None):
    return [d.pop(k, default) for k in keys]


def groupby_count(i, key=None, force_keys=None):
    """
    Example::

        [1,1,1,2,3] -> [(1,3),(2,1),(3,1)]
    """
    counter = defaultdict(lambda: 0)
    if not key:
        key = lambda o: o

    for k in i:
        counter[key(k)] += 1

    if force_keys:
        for k in force_keys:
            counter[k] += 0

    return counter.items()


def groupby_dict(i, keyfunc=None):
    return dict((k, list(v)) for k,v in groupby(sorted(i, key=keyfunc), keyfunc))


def iterate_date(start, stop=None, step=datetime.timedelta(days=1)):
    while not stop or start <= stop:
        yield start
        start += step


def iterate_chunks(i, size=10):
    """
    Iterate over an iterator ``i`` in ``size`` chunks, yield chunks.
    Similar to pagination.

    Example::

        list(iterate_chunks([1,2,3,4], size=2)) -> [[1,2],[3,4]]
    """
    accumulator = []

    for n, i in enumerate(i):
        accumulator.append(i)
        if (n+1) % size == 0:
            yield accumulator
            accumulator = []

    if accumulator:
        yield accumulator


def iterate_flatten(q):
    """
    Flatten nested lists.

    Useful for flattening one-value tuple rows returned from a database query.

    Example::

        [("foo",), ("bar",)] -> ["foo", "bar"]

        [[1,2,3],[4,5,6]] -> [1,2,3,4,5,6]

    """

    return chain.from_iterable(q)


def iterate_date_values(d, start_date=None, stop_date=None, default=0):
    """
    Convert (date, value) sorted lists into contiguous value-per-day data sets. Great for sparklines.

    Example::

        [(datetime.date(2011, 1, 1), 1), (datetime.date(2011, 1, 4), 2)] -> [1, 0, 0, 2]

    """
    dataiter = iter(d)
    cur_day, cur_val = next(dataiter)

    start_date = start_date or cur_day

    while cur_day < start_date:
        cur_day, cur_val = next(dataiter)

    for d in iterate_date(start_date, stop_date):
        if d != cur_day:
            yield default
            continue

        yield cur_val
        try:
            cur_day, cur_val = next(dataiter)
        except StopIteration, e:
            if not stop_date:
                raise


def convert_exception(from_exception, to_exception, *to_args, **to_kw):
    """
    Decorator: Catch exception ``from_exception`` and instead raise ``to_exception(*to_args, **to_kw)``.

    Useful when modules you're using in a method throw their own errors that you want to
    convert to your own exceptions that you handle higher in the stack.

    Example:

    class FooError(Exception):
        pass

    class BarError(Exception):
        pass

    @convert_exception(FooError, BarError, message='bar')
    def throw_foo():
        raise FooError('foo')

    try:
        throw_foo()
    except BarError, e:
        assert e.message == 'bar'
    """
    def wrapper(fn):

        def fn_new(*args, **kw):
            try:
                return fn(*args, **kw)
            except from_exception, e:
                raise to_exception(*to_args, **to_kw), None, sys.exc_info()[2]

        fn_new.__doc__ = fn.__doc__
        return fn_new

    return wrapper


def number_to_string(n, alphabet):
    """
    Given an non-negative integer ``n``, convert it to a string composed of
    the given ``alphabet`` mapping, where the position of each element in
    ``alphabet`` is its radix value.

    Examples::

        >>> number_to_string(12345678, '01')
        '101111000110000101001110'

        >>> number_to_string(12345678, 'ab')
        'babbbbaaabbaaaababaabbba'

        >>> number_to_string(12345678, string.letters + string.digits)
        'ZXP0'

        >>> number_to_string(12345, ['zero ', 'one ', 'two ', 'three ', 'four ', 'five ', 'six ', 'seven ', 'eight ', 'nine '])
        'one two three four five '

    """
    result = ''
    base = len(alphabet)
    current = int(n)
    while current:
        result = alphabet[current % base] + result
        current = current // base

    return result


def string_to_number(s, alphabet):
    """
    Given a string ``s``, convert it to an integer composed of the given
    ``alphabet`` mapping, where the position of each element in ``alphabet`` is
    its radix value.

    Examples::

        >>> string_to_number('101111000110000101001110', '01')
        12345678

        >>> string_to_number('babbbbaaabbaaaababaabbba', 'ab')
        12345678

        >>> string_to_number('ZXP0', string.letters + string.digits)
        12345678

    """
    base = len(alphabet)
    inverse_alphabet = dict(zip(alphabet, xrange(0, base)))
    n = 0
    exp = 0
    for i in reversed(s):
        n += inverse_alphabet[i] * (base ** exp)
        exp += 1

    return n


def isoformat_as_datetime(s):
    """
    Convert a datetime.datetime.isoformat() string to a datetime.datetime() object.
    """
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')


def truncate_datetime(t, resolution):
    """
    Given a datetime ``t`` and a ``resolution``, flatten the precision beyond the given resolution.

    ``resolution`` can be one of: year, month, day, hour, minute, second, microsecond

    Example::

        >>> t = datetime.datetime(2000, 1, 2, 3, 4, 5, 6000) # Or, 2000-01-02 03:04:05.006000

        >>> truncate_datetime(t, 'day')
        datetime.datetime(2000, 1, 2, 0, 0)
        >>> _.isoformat()
        '2000-01-02T00:00:00'

        >>> truncate_datetime(t, 'minute')
        datetime.datetime(2000, 1, 2, 3, 4)
        >>> _.isoformat()
        '2000-01-02T03:04:00'

    """

    resolutions = ['year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond']
    if resolution not in resolutions:
        raise KeyError("Resolution is not valid: {0}".format(resolution))

    args = []
    for r in resolutions:
        args += [getattr(t, r)]
        if r == resolution:
            break

    return datetime.datetime(*args)

def to_str(obj, encoding='utf-8', **encode_args):
    r"""
    Returns a ``str`` of ``obj``, encoding using ``encoding`` if necessary. For
    example::

        >>> some_str = "\xff"
        >>> some_unicode = u"\u1234"
        >>> some_exception = Exception(u'Error: ' + some_unicode)
        >>> to_str(some_str)
        '\xff'
        >>> to_str(some_unicode)
        '\xe1\x88\xb4'
        >>> to_str(some_exception)
        'Error: \xe1\x88\xb4'
        >>> to_str([u'\u1234', 42])
        "[u'\\u1234', 42]"

    See source code for detailed semantics.
    """
    # We coerce to unicode if '__unicode__' is available because there is no
    # way to specify encoding when calling ``str(obj)``, so, eg,
    # ``str(Exception(u'\u1234'))`` will explode.
    if isinstance(obj, unicode) or hasattr(obj, "__unicode__"):
        # Note: unicode(u'foo') is O(1) (by experimentation)
        return unicode(obj).encode(encoding, **encode_args)

    # Note: it's just as fast to do `if isinstance(obj, str): return obj` as it
    # is to simply return `str(obj)`.
    return str(obj)

def to_unicode(obj, encoding='utf-8', fallback='latin1', **decode_args):
    r"""
    Returns a ``unicode`` of ``obj``, decoding using ``encoding`` if necessary.
    If decoding fails, the ``fallback`` encoding (default ``latin1``) is used.
    
    For example::

        >>> to_unicode('\xe1\x88\xb4')
        u'\u1234'
        >>> to_unicode('\xff')
        u'\xff'
        >>> to_unicode(u'\u1234')
        u'\u1234'
        >>> to_unicode(Exception(u'\u1234'))
        u'\u1234'
        >>> to_unicode([u'\u1234', 42])
        u"[u'\\u1234', 42]"

    See source code for detailed semantics.
    """

    if isinstance(obj, unicode) or hasattr(obj, "__unicode__"):
        return unicode(obj)

    obj_str = str(obj)
    try:
        return unicode(obj_str, encoding, **decode_args)
    except UnicodeDecodeError:
        return unicode(obj_str, fallback, **decode_args)


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
