"""descut version"""

<<<<<<< HEAD
version_tag = (1, 0, 1, 'dev-601736e')
=======
version_tag = (1, 0, 1, 'dev-2cea35d')
>>>>>>> cb9993972620836d0ada3c39ab1711b9ca434607
__version__ = '.'.join(map(str, version_tag[:3]))

if len(version_tag) > 3:
    __version__ = '%s-%s' % (__version__, version_tag[3])
