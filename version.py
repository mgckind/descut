"""descut version"""

version_tag = (1, 1, 2, 'dev- 8274d0f')
__version__ = '.'.join(map(str, version_tag[:3]))

if len(version_tag) > 3:
    __version__ = '%s-%s' % (__version__, version_tag[3])
