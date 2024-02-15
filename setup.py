from setuptools import setup, find_packages
from meqsilhouette import __version__

# Import requirements
# requirements
on_rtd = os.environ.get("READTHEDOCS") == "True"

if on_rtd:
    INSTALL_REQUIRES = ['sphinx-rtd-theme']
else:
    INSTALL_REQUIRES = [
        'mpltools',
        'seaborn',
        'astLib',
        'astropy',
        'termcolor',
        'numpy',
        'matplotlib',
        'simms',
        'casatools==6.5.5.21',
        'casadata', 
        ]

with open("README.rst") as tmp:
    readme = tmp.read()

setup(
    author='Iniyan Natarajan',
    author_email='iniyannatarajan@gmail.com',
    name='meqsilhouette',
    version=__version__,
    description='Synthetic Data Generation for mm-VLBI Observations',
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
    install_requires=INSTALL_REQUIRES,
    keywords='meqsilhouette',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 3.8',
        ],
)
