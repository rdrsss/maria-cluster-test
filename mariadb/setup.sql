/*
 * Setup users for test cluster
 * Create users to mysql.user table 
 * Create HAPROXY users, you should probably specificy the actual host.
 */
CREATE USER 'haproxy_check'@'%' IDENTIFIED BY 'password';
CREATE USER 'haproxy_root'@'%' IDENTIFIED BY 'password' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON *.* TO 'haproxy_root'@'%';
FLUSH PRIVILEGES; -- reload user table

