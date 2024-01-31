Introduction
============

Installation
------------

To install **xtask**, run the following command:

.. code-block:: console

	pip install xtask

Usage
-----

Once installed, **xtask** can be invoked from the command line like so:

.. code-block:: console
	:caption: Show all tasks

	xtask -h

.. code-block:: console
	:caption: Run a task

	xtask <task>

.. note::
	The ``xtask`` command will automatically search the working directory and parent directories until it finds an **xtask.project** file which defines some basic configuration 
	settings. It will then use the directory of the **xtask.project** file as a starting point to generate a dependency graph of all tasks that can be found within subdirectories.
	If no **xtask.project** file can be found in the working directory or any parent directory, then the current working directory will be used as a starting point.

	Running ``xtask -h`` will list all available tasks that were found during this process.