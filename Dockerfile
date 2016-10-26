# Matias Carrasco Kind
#
# DES CUT ALL
#

FROM ubuntu:14.04
MAINTAINER Matias Carrasco Kind <mgckind@gmail.com>

#ENVS
ENV HOME /root
ENV SHELL /bin/bash
ENV TERM xterm

# BASICS
RUN apt-get update
RUN apt-get install -y git subversion nano git curl nano wget dialog net-tools build-essential vim unzip libaio1 pkg-config
RUN apt-get install -y gfortran zlibc zlib1g zlib1g-dev
RUN apt-get install -y expect
RUN apt-get install -y strace
RUN apt-get install -y screen
RUN apt-get install -y supervisor # Installing supervisord

# PYTHON 2
RUN apt-get install -y python
RUN apt-get install -y  python-pip python-dev python-numpy 
RUN pip install --upgrade pip


#EUPS
RUN curl -O http://desbuild.cosmology.illinois.edu/desdm_eupsinstall.py
COPY run_eups.py /run_eups.py
RUN python run_eups.py
ENV EUPS_PATH /eups/packages/
ENV EUPS_PKGROOT http://desbuild.cosmology.illinois.edu/eeups/webservice/repository
ENV EUPS_DIR /eups/1.2.30/
ENV SVNROOT https://dessvn.cosmology.illinois.edu/svn/desdm/devel
ENV CC gcc

#SVN TRICK
COPY expect.sh /usr/bin/expect.sh
RUN chmod a+x /usr/bin/expect.sh
RUN ["expect.sh","anonymous","anonymous"]

#INSTALL EUPS PACKAGES BY HAND
#BASIC EUPS PACKAGES
RUN /eups/1.2.30/bin/eups distrib install libjpeg 8d+0
RUN /eups/1.2.30/bin/eups distrib install oracleclient 11.2.0.3.0+4
RUN /eups/1.2.30/bin/eups distrib install stiff 2.7.0+0

#ENVS for Oracle
ENV PATH /eups/packages/Linux64/oracleclient/11.2.0.3.0+4:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/eups/1.2.30/bin
ENV LD_LIBRARY_PATH /eups/packages/Linux64/oracleclient/11.2.0.3.0+4/

#PYTHON 3
RUN apt-get update
RUN apt-get install -y python3
RUN apt-get install -y  python3-pip python3-dev 
RUN apt-get install -y python3-numpy  
RUN pip3 install --upgrade pip
RUN pip3 install  numpy==1.9.0
RUN pip3 install cx_Oracle
RUN pip3 install requests
RUN pip3 install easyaccess
RUN pip3 install tornado
RUN pip3 install celery
RUN pip3 install fitsio==0.9.8
RUN pip3 install astropy==1.2.1
RUN pip3 install pandas


#PYTHON 2 extras
RUN pip install cx_Oracle
RUN pip install fitsio
RUN pip install pandas


#makeDESthumbs
RUN mkdir -p /test/build
WORKDIR /test/build
RUN cd /test/build
RUN svn co $SVNROOT/despyastro/tags/0.3.8/ .
RUN python setup.py install
RUN cd ..
WORKDIR /test
RUN rm -rf build/
RUN git clone  https://opensource.ncsa.illinois.edu/bitbucket/scm/desdm/desthumbs.git
RUN cd /test/desthumbs
WORKDIR  /test/desthumbs
RUN python setup.py install
RUN cd ..
WORKDIR /test
RUN rm -rf desthumbs/

# ENV for DESTHUMBS
ENV DESTHUMBS_DIR /des

#setup stiff
ENV PATH $PATH:/eups/packages/Linux64/stiff/2.7.0+0/bin:/eups/packages/Linux64/oracleclient/11.2.0.3.0+4:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/eups/1.2.30/bin:/eups/packages/Linux64/tiff/4.0.3+1/bin:/eups/packages/Linux64/libjpeg/8d+0/bin
ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:/eups/packages/Linux64/stiff/2.1.3+1/lib:/eups/packages/Linux64/oracleclient/11.2.0.3.0+4/:/eups/packages/Linux64/tiff/4.0.3+1/lib:/eups/packages/Linux64/libjpeg/8d+0/lib

# REDIS 
RUN \
  cd /tmp && \
  wget http://download.redis.io/redis-stable.tar.gz && \
  tar xvzf redis-stable.tar.gz && \
  cd redis-stable && \
  make && \
  make install && \
  cp -f src/redis-sentinel /usr/local/bin 

#working directory
RUN mkdir -p /des
WORKDIR /des
RUN cd /des
WORKDIR /test

#PORTS
EXPOSE 6379

#MONGO
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927
RUN echo "deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.2 multiverse" |  tee /etc/apt/sources.list.d/mongodb-org-3.2.list
RUN apt-get update
RUN sudo apt-get install -y mongodb-org

#Extra installation
RUN apt-get install -y imagemagick
RUN pip3 install redis
RUN pip3 install -U celery[redis]
RUN pip3 install -U flower
RUN pip3 install  Pillow
RUN pip3 install  pymongo
RUN pip3 install  pyfits
RUN pip3 install  prettytable
RUN pip3 install git+https://github.com/mailgun/expiringdict.git


ENV C_FORCE_ROOT true
ADD supervisord.conf /etc/supervisor/conf.d/supervisord.conf
ADD descut /des/descut 
ADD ranC.tck /des/descut/ranC.tck
RUN cd /des/descut
WORKDIR /des/descut
COPY celeryconfig.py /des/descut/celeryconfig.py
RUN mkdir -p /des/descut/workers/

CMD ["/usr/bin/supervisord"]


