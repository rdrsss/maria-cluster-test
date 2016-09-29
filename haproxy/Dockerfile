FROM haproxy:1.6
# Create haproxy user
#RUN useradd -ms /bin/bash haproxy
#USER haproxy
#WORKDIR /home/haproxy
# Copy cfg file
COPY haproxy.cfg /usr/local/etc/haproxy/haproxy.cfg
# Expose port
#EXPOSE 3306
#
#RUN mkdir  /var/lib
RUN mkdir  /var/lib/haproxy


