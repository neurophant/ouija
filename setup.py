from setuptools import setup
from codecs import open
from os import path


here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ouija',
    version='1.0.0',
    description='Python library for building and accessing UDP-relayed TCP proxies',
    long_description=long_description,
    url='https://github.com/neurophant/ouija/',
    author='Anton Smolin',
    author_email='smolin.anton@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: AsyncIO',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.11',
        'Topic :: Internet :: Proxy Servers',
        'Topic :: Software Development :: Libraries',
    ],
    keywords='asyncio https tcp udp proxy relay network encrypted security censorship',
    packages=['ouija'],
    install_requires=['cryptography>=41.0.2', 'pbjson>=1.18.0'],
)
