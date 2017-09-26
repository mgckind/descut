#!/bin/bash
echo -n Please enter mysql root password for upload to k8s secret:
read  rootpw
echo
kubectl create secret generic dessql-config  --from-literal=passwd=$rootpw
