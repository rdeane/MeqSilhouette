FROM ubuntu:20.04 AS spython-base

LABEL "APPLICATION_NAME_BASE"="Ubuntu LTS + MeqSilhouette + dependencies"
LABEL "OS_VERSION"="20.04"
LABEL "SYSTEM_NAME"="MeqSv2"
LABEL "SYSTEM_URL"="https://github.com/rdeane/MeqSilhouette"
LABEL "AUTHOR_NAME"="Iniyan Natarajan, Robin Hall"
LABEL "AUTHOR_EMAIL"="iniyannatarajan@gmail.com, robin@idia.ac.za"

# make opt directory for installs
RUN mkdir -p /opt

# ensure no interaction for tzdata in casa install
ENV DEBIAN_FRONTEND=noninteractive

# install utility packages and repositories
RUN apt-get update -y
RUN apt-get install -y wget vim python3-pip gcc python3 unzip git time
RUN pip uninstall -y enum34
RUN apt-get install -y build-essential cmake g++ rsync libboost-python-dev \
    libboost-program-options-dev texlive-latex-extra texlive-fonts-recommended dvipng cm-super

# build aatm manually
RUN cd
RUN cd /opt
RUN wget -c https://launchpad.net/aatm/trunk/0.5/+download/aatm-0.5.tar.gz
RUN tar -xzf aatm-0.5.tar.gz
RUN cd aatm-0.5 && ./configure && make && make install

# register kern 7
RUN apt-get install -y software-properties-common
RUN add-apt-repository -s ppa:kernsuite/kern-7
RUN apt-add-repository multiverse
RUN apt-add-repository restricted

# install numpy==1.21 to avoid the error "numpy has no attribute 'BitGenerator' and 'asscalar'"
#RUN pip install numpy==1.21

# install required packages
RUN apt-get install -y \
    meqtrees \
    meqtrees-timba \
    tigger-lsm \
    python3-astro-tigger \
    python3-astro-tigger-lsm \
    casalite \
    wsclean \
    pyxis \
    python3-casacore

# install numpy==1.21 to avoid the error "numpy has no attribute 'BitGenerator' and 'asscalar'"
RUN pip install numpy==1.21

RUN apt-get clean

# update casa data
RUN casa-config --exec update-data

# download and install MeqSilhouette from master
RUN cd
RUN cd /opt
RUN git clone --depth 1 https://github.com/rdeane/MeqSilhouette.git
RUN cd MeqSilhouette && pip install .
RUN cd

ENV MEQTREES_CATTERY_PATH=/usr/lib/python3/dist-packages/Cattery
ENV PATH=/usr/local/bin:$PATH
ENV PYTHONPATH=/usr/local/lib/python3.8/dist-packages:/usr/lib/python3/dist-packages
ENV LC_ALL=C
