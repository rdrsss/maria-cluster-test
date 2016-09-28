FROM ubuntu:14.04

# Update apt's start policy
RUN \
	echo exit 101 > /usr/sbin/policy-rc.d && \
	chmod +x /usr/sbin/policy-rc.d

# Add user to mysql
RUN \
	groupadd -r mysql && \
	useradd -r -g mysql mysql

# run an update
RUN apt-get update

# Add maria depots
RUN \
	DEBIAN_FRONTEND=noninteractive apt-get install software-properties-common -y && \
	apt-key adv --recv-keys --keyserver hkp://keyserver.ubuntu.com:80 0xcbcb082a1bb943db && \
	add-apt-repository 'deb [arch=amd64,i386,ppc64el] http://ftp.utexas.edu/mariadb/repo/10.1/ubuntu trusty main'

# Install latest maria 10.1.x
RUN \
	apt-get update && \
	DEBIAN_FRONTEND=noninteractive apt-get install mariadb-server -y

# Make volume
VOLUME ["/etc/mysql", "/var/lib/mysql", "/data"]

# Expose port
EXPOSE 3306

# Copy config file
COPY my.cnf /etc/mysql/

# Copy setup file
COPY setup.sql /

# Run
CMD ["mysqld"]
