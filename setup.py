from setuptools import setup

setup(name='jackd_status',
    version='0.1',
    description='jackd StatusIcon for the Xfce Panel',
    url='http://github.com/cbrown1/jackd_status',
    author='Christopher Brown',
    author_email='cbrown1@pitt.edu',
    license='GPL3',
    packages=['jackd_status'],
    zip_safe=False,
    entry_points = {
        'console_scripts': ['jackd_status=jackd_status:main']
    },
      classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Environment :: Console",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Physics",
        "Natural Language :: English",
        ],
)

