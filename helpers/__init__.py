def decode(string):
    for i in ['utf-8', 'cp1252']:
        try:
            return string.decode(i)
        except UnicodeEncodeError:
            pass
    return string


def encode(string):
    for i in ['utf-8', 'cp1252']:
        try:
            return string.encode(i)
        except UnicodeEncodeError:
            pass
    return string


def strargs(args):
    if len(args) == 0:
        return ''
    else:
        rv = '?'
        for key in args:
            rv += key
            if args.get(key):
                rv += '=' + args[key]
            rv += '&'
        return decode(rv[:-1])


def url_extention(item_name):
    if item_name:
        return '/' + decode(item_name)
    else:
        return ''


class link(object):
    def __init__(self, url, name):
        self.url = url
        self.name = name


class piclink(link):
    def __init__(self, url, name, pic):
        link.__init__(self, url, name)
        self.pic = pic
