Facilitate
==========

Installation
------------

Before beginning, you will need to install Python 3.11 and `Poetry <https://python-poetry.org>`_.
Once you have the necessary prerequisites, you can install the project by running the following command:

.. code:: shell

    poetry install

HTTP API
--------

Facilitate provides a simple HTTP API.
That API is served by a Flask server that can either be deployed locally or to AWS Lambda via Zappa (i.e., serverless).

:code:`PUT /diff`
~~~~~~~~~~~~~~~~~

Computes an edit script that transforms one Scratch program into another program.

**Payload:**

.. code:: json

    {
        "from_program": ...,
        "to_program": ...
    }

:code:`PUT /distance`
~~~~~~~~~~~~~~~~~~~~~

Computes a weighted edit distance from one Scratch program to another program.

**Payload:**

.. code:: json

    {
        "from_program": ...,
        "to_program": ...
    }

:code:`PUT /progress`
~~~~~~~~~~~~~~~~~~~~~

Computes the progress of a student program towards a set of acceptable reference solutions.
Progress is represented as the weighted edit distance from the student program to each reference solution.

**Payload:**

.. code:: json

    {
        "program": ...,
        "solutions": [
            {

            },
            ...
        ]
    }


Deployment
----------

Local Deployment via Flask
~~~~~~~~~~~~~~~~~~~~~~~~~~

To deploy the server locally via Flask, run the following command:

.. code:: shell

    poetry run flask --app facilitate.server run

While the server is running, you can use the example script to simulate a call to the /diff endpoint:

.. code:: shell

    poetry run scripts/invoke-diff.py

Production Deployment via AWS Lambda and Zappa
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To deploy the server to production (AWS Lambda) via Zappa, run the following command:

.. code:: shell

    poetry run zappa deploy

To undeploy the server from production, run the following command:

.. code:: shell

    poetry run zappa undeploy

Command-Line Tools
------------------

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

:code:`diff`
~~~~~~~~~~~~

The :code:`diff` command is used to compute an edit script that transforms one Scratch program into another.
It takes the path to two JSON-formatted Scratch program as input (:code:`before` and :code:`after`, respectively) and outputs the edit script to the specified output path (:code:`-o` / :code:`--output`).

.. code:: shell

    poetry run facilitate diff examples/bad.json examples/good.json -o diff.json

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

Additionally, the :code:`facilitate` command-line interface provides a fuzzer.
To use the fuzzer to attempt to parse all programs within a given directory:

.. code:: shell

    poetry run facilitate fuzz parse -i programs -o crashes.csv

The above command will find all the `.json` program files within the specified directory, attempt to parse them, and log any programs that cause the parser to crash to the specified output CSV file.

To use the fuzzer to attempt to diff all successive pairs of student programs within a given directory:

.. code:: shell

    poetry run facilitate fuzz diff -i programs -o crashes.csv
