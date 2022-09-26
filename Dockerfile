FROM ubuntu:18.04 AS spython-base

LABEL "APPLICATION_NAME_BASE"="Ubuntu LTS + MeqSilhouette + dependencies"
LABEL "OS_VERSION"="18.04"
LABEL "SYSTEM_NAME"="MeqSv2"
LABEL "SYSTEM_URL"="https://github.com/rdeane/MeqSilhouette"
LABEL "AUTHOR_NAME"="Iniyan Natarajan, Robin Hall"
LABEL "AUTHOR_EMAIL"="iniyan.natarajan@wits.ac.za, robin@idia.ac.za"

# make opt directory for installs
RUN mkdir -p /opt

# ensure no interaction for tzdata in casa install
ENV DEBIAN_FRONTEND=noninteractive

# install utility packages and repositories
RUN apt-get update -y
RUN apt-get install -y wget vim python-pip gcc python unzip git time
RUN pip uninstall -y enum34
RUN apt-get install -y build-essential cmake gfortran g++ libncurses5-dev \
    libreadline-dev flex bison libblas-dev liblapacke-dev libcfitsio-dev \
    wcslib-dev libfftw3-dev libhdf5-serial-dev rsync \
    libboost-python-dev libboost-program-options-dev libboost-program-options1.65.1 \
    libboost-program-options1.65-dev libpython2.7-dev libxml2-dev libxslt1-dev \
    texlive-latex-extra texlive-fonts-recommended dvipng

# build aatm manually
RUN cd
RUN cd /opt
RUN wget -c https://launchpad.net/aatm/trunk/0.5/+download/aatm-0.5.tar.gz
RUN tar -xzf aatm-0.5.tar.gz
RUN cd aatm-0.5 && ./configure && make && make install

# install kern 6
RUN apt-get install -y software-properties-common
RUN add-apt-repository -s ppa:kernsuite/kern-6
RUN apt-add-repository multiverse
RUN apt-add-repository restricted

# install required packages
RUN apt-get install -y \
    meqtrees \
    meqtrees-timba \
    tigger \
    tigger-lsm \
    python-astro-tigger \
    python-astro-tigger-lsm \
    casalite \
    wsclean \
    pyxis \
    python-casacore

RUN apt-get clean

# update casa data
RUN casa-config --exec update-data

# download and install MeqSilhouette from master
RUN cd
RUN cd /opt
RUN git clone --depth 1 https://github.com/rdeane/MeqSilhouette.git
RUN cd MeqSilhouette && pip install .
RUN cd

ENV MEQTREES_CATTERY_PATH=/usr/lib/python2.7/dist-packages/Cattery
ENV PATH=/usr/local/bin:$PATH
ENV PYTHONPATH=/usr/lib/python2.7/dist-packages
ENV LC_ALL=C
