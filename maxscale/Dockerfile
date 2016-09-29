FROM ubuntu:14.04

# install dependencies
RUN \
	DEBIAN_FRONTEND=noninteractive apt-get install -y wget && \
	DEBIAN_FRONTEND=noninteractive apt-get install -y libcurl3

# Grab deb file for MaxScale
RUN wget https://downloads.mariadb.com/MaxScale/2.0.0/ubuntu/dists/trusty/main/binary-amd64/maxscale-beta-2.0.0-1.ubuntu.trusty.x86_64.deb 

# Install MaxScale
RUN \
	dpkg -i maxscale-beta-2.0.0-1.ubuntu.trusty.x86_64.deb && \
	apt-get install -f


