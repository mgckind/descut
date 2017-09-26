- Create PV
- Create PVC
- Create Secrets for Redis
    kubectl create secret generic redis-conf --from-file=redis/redis.conf
- Deploy Redis
- Create Secret for mysql
    sh mysql-secret.sh
- Deploy mysql
- Copy mysql cluster ip into mysqlconfig.yaml
- Create Secrets for Celery and easyweb
    kubectl create secret generic easyw-conf --from-file=easyweb/ranC.tk --from-file=easyweb/celeryconfig.py --from-file=easyweb/mysqlconfig.yaml
- Deploy easyweb (and monitor)
