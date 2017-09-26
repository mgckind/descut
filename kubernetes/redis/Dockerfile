# REDIS
FROM ubuntu:16.04
MAINTAINER Matias Carrasco Kind <mgckind@gmail.com>

RUN apt-get update
RUN apt-get install -y git subversion nano git curl nano wget dialog net-tools build-essential vim
#Supervisor, only way to make the deamon work
RUN apt-get install -y supervisor
RUN mkdir -p /var/log/supervisor

# Install Redis.
RUN \
  cd /tmp && \
  wget http://download.redis.io/redis-stable.tar.gz && \
  tar xvzf redis-stable.tar.gz && \
  cd redis-stable && \
  make && \
  make install && \
  cp -f src/redis-sentinel /usr/local/bin && \
  mkdir -p /etc/redis && \
  rm -rf /tmp/redis-stable*

# Expose ports.
EXPOSE 6379

RUN mkdir -p /des/easyweb/redis/
#ADD redis.conf /etc/redis/redis.conf

#ADD supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN echo "[supervisord]" >> /etc/supervisor/conf.d/supervisord.conf
RUN echo "nodaemon=true" >> /etc/supervisor/conf.d/supervisord.conf
RUN echo "[program:redis]" >> /etc/supervisor/conf.d/supervisord.conf
RUN echo 'command=/bin/bash -c "redis-server /etc/redis/redis.conf"' >> /etc/supervisor/conf.d/supervisord.conf


## Using supervisor as entry point
ENTRYPOINT ["/usr/bin/supervisord"]
