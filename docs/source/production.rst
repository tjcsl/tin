#############
Deploying Tin
#############

.. note::

   This page is intended for the lead(s) of Tin.
   This information may be irrelevant for others.


Backing Up Data
---------------
You can back up media with

.. code-block:: bash

    rsync -ah root@tin.csl.tjhsst.edu:/home/tin/tin/tin/media/ /path/to/backup/

You can then back up the database with

.. code-block:: bash

    python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e admin -e auth.Permission > export_YYYY_MM_DD.json
    # copy to local machine
    iconv -f ISO-8859-1 -t UTF-8 export_YYYY_MM_DD.json > export_YYYY_MM_DD_utf8.json
    python manage.py loaddata export_YYYY_MM_DD_utf8.json

