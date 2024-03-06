Facilitate
==========

Installation
------------

Before beginning, you will need to install Python 3.12 and [Poetry](https://python-poetry.org).
Once you have the necessary prerequisites, you can install the project by running the following command:

.. code:: shell

    poetry install

Server
------

Deployment: Local via Flask
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To deploy the server locally via Flask, run the following command:

.. code:: shell

    poetry run flask --app facilitate.server run

While the server is running, you can use the example script to simulate a call to the /diff endpoint:

.. code:: shell

    poetry run scripts/invoke-diff.py

Deployment: Production via AWS Lambda and Zappa
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To deploy the server to production (AWS Lambda) via Zappa, run the following command:

.. code:: shell

    poetry run zappa deploy

To undeploy the server from production, run the following command:

.. code:: shell

    poetry run zappa undeploy
