Facilitate
==========

Installation
------------

Before beginning, you will need to install Python 3.12 and [Poetry](https://python-poetry.org).
Once you have the necessary prerequisites, you can install the project by running the following command:

.. code:: shell

    poetry install

Testing
-------

To run the regression tests, linters, and type checking, run the following command:

.. code:: shell

    make check

To only run the regression tests, run the following command:

.. code:: shell

    make test

To only run the linter and type checker, run the following command:

.. code:: shell

    make lint

Server
------

Facilitate provides a simple web server that is used to compute edit scripts between Scratch programs.
The server exposes a single endpoint, GET /diff, that accepts two Scratch programs within a JSON payload and returns the edit script between the two programs.

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
