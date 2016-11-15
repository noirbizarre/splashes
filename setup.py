#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Elasticsearch loader and playground for SIRENE dataset
"""
import io
import os
import re

from setuptools import setup, find_packages

ROOT = os.path.dirname(__file__)

RE_CODE_BLOCK = re.compile(r'```(?P<language>\w+)?\n(?P<lines>.*?)```', re.S)
RE_SELF_LINK = re.compile(r'\[(.*?)\]\[\]')
RE_LINK_TO_URL = re.compile(r'\[(?P<text>.*?)\]\((?P<url>.*?)\)')
RE_LINK_TO_REF = re.compile(r'\[(?P<text>.*?)\]\[(?P<ref>.*?)\]')
RE_LINK_REF = re.compile(r'^\[(?P<key>[^!].*?)\]:\s*(?P<url>.*)$', re.M)
RE_IMAGE = re.compile(r'\!\[(?P<text>.*?)\]\((?P<url>.*?)\)')
RE_TITLE = re.compile(r'^(?P<level>#+)\s*(?P<title>.*)$', re.M)
RE_CODE = re.compile(r'``([^<>]*?)``')

RST_TITLE_LEVELS = ['=', '-', '~']

GITHUB_REPOSITORY = 'https://github.com/noirbizarre/splashes'


def md2pypi(filename):
    '''
    Load .md (markdown) file and sanitize it for PyPI.
    '''
    content = io.open(filename).read()

    # Code blocks
    for match in RE_CODE_BLOCK.finditer(content):
        rst_block = '\n'.join(
            ['.. code-block:: {language}'.format(**match.groupdict()), ''] +
            ['    {0}'.format(l) for l in match.group('lines').split('\n')] +
            ['']
        )
        content = content.replace(match.group(0), rst_block)

    # Images
    for match in RE_IMAGE.finditer(content):
        url = match.group('url')
        if not url.startswith('http'):
            url = '/'.join((GITHUB_REPOSITORY, 'raw/master', url))

        rst_block = '\n'.join([
            '.. image:: {0}'.format(url),
            '  :alt: {0}'.format(match.group('text'))
        ])
        content = content.replace(match.group(0), rst_block)

    # Links
    refs = dict(RE_LINK_REF.findall(content))
    content = RE_LINK_REF.sub('.. _\g<key>: \g<url>', content)
    content = RE_SELF_LINK.sub('`\g<1>`_', content)
    content = RE_LINK_TO_URL.sub('`\g<text> <\g<url>>`_', content)
    for match in RE_LINK_TO_REF.finditer(content):
        content = content.replace(match.group(0), '`{text} <{url}>`_'.format(
            text=match.group('text'),
            url=refs[match.group('ref')]
        ))

    # Inline <code>
    content = RE_CODE.sub('``\g<1>``', content)

    # Titles
    for match in RE_TITLE.finditer(content):
        level = len(match.group('level')) - 1
        underchar = RST_TITLE_LEVELS[level]
        title = match.group('title')
        underline = underchar * len(title)

        full_title = '\n'.join((title, underline))
        content = content.replace(match.group(0), full_title)

    return content


# Get the long description from the README file
long_description = md2pypi('README.md')

requirements = io.open(os.path.join(ROOT, 'requirements.pip')).readlines()

setup(
    name='splashes',
    version='0.1.0.dev',
    url=GITHUB_REPOSITORY,
    license='MIT',
    author='Axel Haustant',
    author_email='axel.haustant@data.gouv.fr',
    description=__doc__,
    long_description=long_description,
    packages=find_packages(),
    zip_safe=False,
    platforms='any',
    install_requires=requirements,
    keywords='sirene elasticsearch cli',
    entry_points={
        'console_scripts': [
            'splashes = splashes.cli:main',
        ],
    },
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
