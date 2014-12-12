from setuptools import setup, find_packages

version = '0.1dev0'

setup(
    name='rio',
    version=version,
    author='Jasper Spaans',
    author_email='j@jasper.es',
    description='Run It Once',
    packages=find_packages('.'),
    install_requires=[
        'Twisted',
        'cached_property',
        'setuptools',
    ],
    entry_points={
        'console_scripts': [
            'riod = rio.main:main',
        ],
    },
)
