Facilitate
==========

Installation
------------

Before beginning, you will need to install Python 3.11 and [Poetry](https://python-poetry.org).
Once you have the necessary prerequisites, you can install the project by running the following command:

.. code:: shell

    poetry install

Usage: Command-Line Interface
-----------------------------

Facilitate provides a command-line interface that is mostly intended for debugging and development purposes.
To obtain a list of commands exposed by the CLI, run the following command:

.. code:: shell

    poetry run facilitate --help

:code:`draw`
~~~~~~~~~~~~

The :code:`draw` command is used to visualize the AST of a Scratch program.
It takes the path to a JSON-formatted Scratch program as input and outputs either a PNG or PDF (:code:`-f` / :code:`--format`) visualization of that program to the specified output path (:code:`-o` / :code:`--output`).

.. code:: shell

    poetry run facilitate draw examples/bad.json -f pdf -o ast.bad.pdf

Usage: Server
-------------

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

Additionally, the :code:`facilitate` command-line interface provides a fuzzer, described in the Command-Line Interface section.

