/*
 * Setup users for test cluster
 * Create users to mysql.user table 
 * Create HAPROXY users, you should probably specificy the actual host.
 */
CREATE USER IF NOT EXISTS 'maxscale'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON *.* TO 'maxscale'@'%';
FLUSH PRIVILEGES; -- reload user table

