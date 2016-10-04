# descut services

This repository contains most of the code needed to run the DES cutout services which allows to create cutouts from coadd images as well as single epoch images.

### Software description 

There are several software and packages used both in the front-end and back-end.

#### Front-end

- We use [tornado](http://www.tornadoweb.org/en/stable/) as a Web Server
- We use [Polymer](https://www.polymer-project.org/1.0/) for web pages design and interfaces
- We use [Flower](http://flower.readthedocs.io/en/latest/) to monitor jobs submitted 

#### Back-end

- We use [Redis](http://redis.io/) for storing the jobs and user information and broker for celery
- We use [MongoDB](https://www.mongodb.com/) for storing information regarding the images 
- We use [Oracle DB](https://www.oracle.com/index.html) which is the default DES DB
- We use [Celery](http://www.celeryproject.org/) as a queue and job manager
- Many other python tools ([easyaccess](https://github.com/mgckind/easyaccess), [astropy](http://www.astropy.org/), [pandas](http://pandas.pydata.org/), , [fitsio](https://github.com/esheldon/fitsio), and others)


Everything is containerized  and deployed using [Docker](https://www.docker.com/).
