#!/usr/bin/env bash

# bootstrap.sh - setup an EC2 instance

yum install nginx -y

/bin/systemctl start  nginx.service

cat << EOF > /usr/share/nginx/html/index.html
<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>Hello World</title></head><body><h1>Hello World</h1>
<h2>Hostname: `hostname`</h2></body></html>

EOF
