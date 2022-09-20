from setuptools import setup, find_packages
from meqsilhouette import __version__

with open("README.rst") as tmp:
    readme = tmp.read()

setup(
    author='Iniyan Natarajan',
    author_email='iniyan.natarajan@wits.ac.za',
    name='meqsilhouette',
    version=__version__,
    description='VLBI Observation Simulator',
    long_description=readme,
    long_description_content_type="text/x-rst",
    url='https://github.com/rdeane/MeqSilhouette',
    license='GNU GPL v2',
    packages=find_packages(include=['meqsilhouette','meqsilhouette.*']),
    package_data={
        'meqsilhouette': ['data/*','data/ANTENNA_EHT2017/*','framework/tdlconf.profiles'],
        },
    entry_points={
        'console_scripts': ['meqsilhouette=meqsilhouette.driver.run_meqsilhouette:run_meqsilhouette']
    },
    install_requires=[
        'mpltools',
        'seaborn',
        'astLib',
        'astropy',
        'termcolor',
        'numpy',
        'matplotlib',
        'pyfits',
        'simms',
        ],
    keywords='meqsilhouette',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 2.7',
        ],
)
