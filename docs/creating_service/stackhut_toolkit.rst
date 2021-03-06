.. _creating_toolkit:

StackHut Toolkit
================


.. Introduction
.. ------------

The StackHut Toolkit is used to create, test, deploy, and maintain your services hosted on StackHut.
It provides a range of commands used to interact with your code and the StackHut servers.

Getting Started
^^^^^^^^^^^^^^^

Firstly, install the Toolkit and requirements by following the instructions in :ref:`getting_started_installation`. 

**Quick Install**

.. code:: bash

    sudo pip3 install stackhut
    
**Upgrade**

.. code:: bash

    sudo pip3 install --upgrade stackhut

.. note:: Things move pretty quickly on the Toolkit so if you find an error try upgrading first to see if it's been fixed. Thanks!

Usage
-----

Having installed the Toolkit just make sure it's accessible from your path

.. code:: bash
    
    $ stackhut -V
    > stackhut 0.5.4

Now that's done, you may wish to run through the tutorial at :ref:`tutorial_create`.

We've tried to make the Toolkit as easy to use as possible and it follows the ``git`` and ``docker`` command based model, e.g. ``stackhut init``, etc.
You can find the list of commands and options available by running,

.. code:: bash

    $ stackhut --help

.. note:: Enable verbose mode to view more debug output using ``stackhut -v``.

Commands
--------

In this section we'll go over the main commands supported by the Toolkit and explain their use in helping you to build, test, deploy and maintain your services locally and in the cloud.

Help for any command can be displayed by running,

.. code:: bash

    $ stackhut command --help


``login``
^^^^^^^^^

.. code:: bash

    $ stackhut login

This command logins you into the StackHut platform using your GitHub username and StackHut password.
You need to be logged to build and deploy service (this is so we know how to correctly name the image when building the service),

.. note:: Your details are stored in a user-only readable file at ``$HOME/.stackhut.cfg``.


``logout``
^^^^^^^^^^

.. code:: bash

    $ stackhut logout

Logs you out of the StackHut platform.

``info``
^^^^^^^^

.. code:: bash

    $ stackhut info

Displays information regarding the Toolkit version, Docker version, and current logged-in user.

``init``
^^^^^^^^
.. code:: bash

    $ stackhut init baseos stack [--no-git]

============    ===========
Option          Description
============    ===========
``baseos``      The base operating system to use, e.g. fedora, alpine, ubuntu, etc.
``stack``       The default language stack to use, e.g. python, nodejs, etc.
``--no-git``    Disables creating a git repo as part of the init process
============    ===========

Initialises a new StackHut project in the current directory using the specified base Operating System and language stack. This creates a working skeleton project you can modify to rapidly build your own service. 

By default it creates a service in your stack that has a single ``add`` function already specified. The initial project is comprised of the following files,

* a minimal ``Hutfile`` (see :ref:`creating_structure_hutfile`),
* an ``api.idl`` inteface definition file (see :ref:`creating_app_idl`),
* an ``app.py`` application file (or app.js, etc.),
* a ``README.md`` markdown file,
* a ``test_request.json`` test file to simulate requests to your service,
* an empty packages file for your chosen language stack (e.g. ``requirements.txt`` for Python, or ``package.json`` for Node, etc.).

The ``init`` command also creates a git repo and commits the files be default, to disable this behaviour use the ``--no-git`` flag.


``build``
^^^^^^^^^

.. code:: bash

    $ stackhut build [--force]

============    ===========
Option          Description
============    ===========
``--force``     Forces the build to occur even if no file changes 
============    ===========

Builds the image so that it may be tested locally or deployed to the cloud. This command is usually unneeded as both the ``run`` and ``deploy`` commands run a build if needed.

Building a service involves, 
* setting up the base OS and the language stack,
* installing all OS and language packages as specified in the `Hutfile`,
* copying across all files referenced in the `Hutfile`,
* installing the StackHut control runner,
* running any auxiliary commands as specified in the `Hutfile`.

Building can be time-consuming so is performed on an as-needed basis by detecting changes to the files referenced from the `Hutfile`. If this fails, or perhaps you're installing software from across the network as part of the build, you may wish to force the build to occur by passing the ``--force`` flag.


``runcontainer``
^^^^^^^^^^^^^^^^

.. code:: bash

    $ stackhut runcontainer [--force]

================    ===========    
Option              Description
================    ===========
``--force``         Forces build before run 
================    ===========


Builds the image and and hosts the service locally on ``http://localhost:4001``. You can test the service either using the client-libaries or by ``curl``-ing the ``test_request.json`` file to the local server, as described in :ref:`using_index`.

Upon running this command the Toolkit will build the image (if required) and run the service within the container. This is exactly the same code as will be run on the hosted StackHut platform so you can be sure that if it works locally it will work in the cloud. Output from running this request is placed in the ``run_result`` directory, with the JSON response object in ``run_result\response.json``.


``runhost``
^^^^^^^^^^^

.. code:: bash

    $ stackhut runhost request_file


The ``runcontainer`` command builds and runs an full image - we make every effort to cache and reduce the time this process takes but you may find it still imposes a delay when testing quick changes. 
To this end we provide the ``runhost`` command - it runs your service immediately using your host operating system and installed dependencies instead.

As with the ``run`` command it hosts the service locally for use with the client-libraries and writes the response into ``run_result``.

This can be a useful way to setup a quick feedback loop, but we recommend using the ``runcontainer`` command in most cases as it will test your entire service and dependencies using the same code as on the server.
Furthermore it can be easier to setup the dependencies for the service in the container and they'll be isolated from the main host OS.

.. note:: ``runhost`` will not install any dependencies from the `Hutfile` for you and you will have to manually set these up if needed.

``deploy``
^^^^^^^^^^

.. code:: bash

    $ stackhut deploy [--force]

================    ===========
Option              Description
================    ===========
``--force``         Forces build before deploy
================    ===========

.. ``--no-build``      Deploy only, do not build or push image first

The deploy command packages and uploads your project to the StackHut platform where it's build remotely and then deployed live under the service address ``username/servicename`` and can be called from ``https://api.stackhut.com/run``. 
Deployment requires that you have an account at StackHut and are logged in using the command line tool.

.. If you've already deployed the image and just want to update the service metadata, e.g. the description, README, API docs, etc., you can run ``deploy`` with the ``--no-build`` flag and it will skip the full deploy - a much quicker operation.

