"""descut version"""

version_tag = (1, 1, 0, 'dev-a1a3b9d')
__version__ = '.'.join(map(str, version_tag[:3]))

if len(version_tag) > 3:
    __version__ = '%s-%s' % (__version__, version_tag[3])
