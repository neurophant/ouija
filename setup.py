from setuptools import setup
from codecs import open
from os import path


here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ouija',
    version='1.3.0',
    description='Python relay/proxy server and library to build reliable encrypted TCP/UDP tunnels for TCP traffic',
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
    keywords='asyncio http https tcp udp proxy tunnel relay network encrypted security censorship',
    packages=['ouija'],
    install_requires=['cryptography>=41.0.2', 'pbjson>=1.18.0', 'numpy>=1.25.2'],
    entry_points={
        'console_scripts': [
            'ouija = ouija.server:main',
            'ouija_secret = ouija.secret:main',
        ]
    }
)
