import unittest

from nose.tools import eq_, raises

from jstestnet.system import useragent
from jstestnet.system.useragent import parse_useragent


def _verify_ua(ua, expectation):
    eq_(sorted(parse_useragent(ua)), sorted(expectation))


def test_useragents():
    for ua, expectation in (
        # Firefox:
        ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0b10) '
         'Gecko/20100101 Firefox/4.0b10',
         [('firefox', '4.0b10'), ('gecko', '2.0b10')]),
        ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; '
         'rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13',
         [('firefox', '3.6.13'), ('gecko', '1.9.2.13')]),
        ('Mozilla/5.0 (X11; U; Linux armv61; en-US; rv:1.9.1b2pre) '
         'Gecko/20081015 Fennec/1.0a1',
         [('fennec', '1.0a1'), ('gecko', '1.9.1b2pre')]),
        ('Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0b7pre) Gecko/20100925 '
         'Firefox/4.0b7pre',
         [('firefox', '4.0b7pre'), ('gecko', '2.0b7pre')]),
        # Chrome:
        ('Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.17 '
         '(KHTML, like Gecko) Chrome/11.0.652.0 Safari/534.17',
         [('applewebkit', '534.17'), ('chrome', '11.0.652.0'),
          ('safari', '534.17')]),
        # Safari:
        ('Mozilla/5.0 (Windows; U; Windows NT 6.1; sv-SE) '
         'AppleWebKit/533.19.4 (KHTML, like Gecko) Version/5.0.3 '
         'Safari/533.19.4',
         [('safari', '533.19.4'), ('applewebkit', '533.19.4')]),
        ('Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_1_2 like Mac OS X; en-us) '
         'AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7D11 '
         'Safari/528.16',
         [('applewebkit', '528.18'), ('mobile-safari', '528.16')]),
        # Android:
        ('Mozilla/5.0 (Linux; U; Android 2.2; en-us; Nexus One Build/FRF91) '
         'AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile '
         'Safari/533.1',
         [('mobile-safari', '533.1'), ('applewebkit', '533.1'),
          ('android', '2.2')]),
        # MSIE:
        ('Mozilla/5.0 (Windows; U; MSIE 9.0; WIndows NT 9.0; en-US))',
         [('msie', '9.0')]),
        ('Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)',
         [('msie', '7.0b')]),
        ('Mozilla/4.0 (compatible; MSIE 6.1; Windows XP; .NET CLR 1.1.4322; '
         '.NET CLR 2.0.50727)',
         [('msie', '6.1')]),
        # Blackberry:
        ('Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en) '
         'AppleWebKit/534.1+ (KHTML, Like Gecko) Version/6.0.0.141 Mobile '
         'Safari/534.1+',
         [('applewebkit', '534.1'), ('blackberry', '6.0.0.141'),
          ('mobile-safari', '534.1')]),
        ('BlackBerry9630/4.7.1.40 Profile/MIDP-2.0 Configuration/CLDC-1.1 '
         'VendorID/105',
         [('blackberry9630', '4.7.1.40')]),
        # Opera:
        ('Opera/9.80 (X11; Linux i686; U; en) Presto/2.9.168 Version/11.51',
         [('opera', '11.51'), ('presto', '2.9.168')]),
    ):
        yield _verify_ua, ua, expectation


@raises(useragent.UnidentifiedBrowser)
def test_unknown_version():
    parse_useragent('GARBAGE')


@raises(useragent.UnidentifiedBrowser)
def test_unknown_browser():
    parse_useragent('GARBAGE; rv:2.0b10')
