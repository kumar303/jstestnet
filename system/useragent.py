import re


class Engine(object):

    def __init__(self, pattern):
        self.pattern = re.compile(pattern)
        self.name = None

    def search(self, ua):
        m = self.pattern.search(ua)
        if not m:
            return []
        return [m.groupdict()]


class Gecko(Engine):

    def __init__(self):
        super(Gecko, self).__init__(r'rv:(?P<version>[0-9a-z\.]+)')

    def search(self, ua):
        results = super(Gecko, self).search(ua)
        if ua.find('gecko') != -1:
            for res in results:
                res['name'] = 'gecko'
            return results
        else:
            return []


class StdEngine(Engine):

    def __init__(self, name):
        super(StdEngine, self).__init__(
                    '(?P<name>%s)[/:\s](?P<version>[0-9a-z\.]+)' % name)


class Blackberry(Engine):

    def __init__(self):
        self.pattern = re.compile(
        r'(?P<name>blackberry\s?[0-9]*[a-z]*)/?(?P<version>[0-9a-z\.]+)?')
        self.alt_vr = re.compile(r'version/(?P<version>[0-9a-z\.]+)')

    def search(self, ua):
        m = self.pattern.search(ua)
        if not m:
            return []
        info = m.groupdict()
        info['name'] = info['name'].replace(' ', '')
        if not info['version']:
            info['version'] = self.alt_vr.search(ua).groupdict()['version']
        return [info]


class SafariVariants(Engine):

    def __init__(self):
        self.engines = [StdEngine('safari'), StdEngine('mobile safari')]

    def search(self, ua):
        variants = []
        for eng in self.engines:
            for info in eng.search(ua):
                if info['name'] == 'mobile safari':
                    info['name'] = 'mobile-safari'
                if 'mobile' in ua:
                    # If it's mobile safari, de-dupe
                    info['name'] = 'mobile-safari'
                if info['name'] not in [i['name'] for i in variants]:
                    variants.append(info)
        return variants


engines = [
    Gecko(),
    StdEngine('applewebkit'),
    StdEngine('firefox'),
    StdEngine('fennec'),
    StdEngine('chrome'),
    SafariVariants(),
    StdEngine('android'),
    StdEngine('msie'),
    StdEngine('webos'),
    StdEngine('presto'),
    StdEngine('konqueror'),
    StdEngine('series60'),
    Blackberry()
]


class UnidentifiedBrowser(Exception):
    """The useragent string of this browser did not match any
    known patterns."""


def parse_useragent(full_useragent):
    ua_string = full_useragent.lower()
    ua_engines = []
    for eng in engines:
        for res in eng.search(ua_string):
            ua_engines.append((res['name'], res['version']))
    if not len(ua_engines):
        raise UnidentifiedBrowser(
                'Could not parse engine/version in useragent string %r' %
                                                        full_useragent)
    return ua_engines
