import sys
from setuptools import setup, find_packages

_PACKAGE_NAME = 'cloudify-aria-extensions'
_PYTHON_SUPPORTED_VERSIONS = [(2, 6), (2, 7)] 

if (sys.version_info[0], sys.version_info[1]) not in _PYTHON_SUPPORTED_VERSIONS:
    raise NotImplementedError('{0} Package support Python version 2.6 & 2.7 Only'.format(_PACKAGE_NAME))

setup(
    name=_PACKAGE_NAME,
    version='0.1',
    description='Integration of Cloudify with ARIA',
    author='Gigaspaces',
    author_email='cosmo-admin@gigaspaces.com',
    license='LICENSE',
    package_dir={'aria_extension_cloudify': 'parser/aria_extension_cloudify',
                 'old_parser_components': 'parser/old_parser_components'},
    packages=find_packages(where='parser',
                           include=['aria_extension_cloudify*', 'old_parser_components*']),
    install_requires=['aria==0.1.0'])

