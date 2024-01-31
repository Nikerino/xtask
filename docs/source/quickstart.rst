Quickstart
==========

This short **xtask** quickstart guide aims to help users get setup and learn about **xtask** for the first time.

Prerequesites
-------------

Using a compatible version of Python (3.10 or newer), install the **xtask** package via pip:

.. code-block:: console

	pip install xtask

Once installed, you should be able to run xtask directly from the command line:

.. code-block:: console

	xtask -h

First Project
-------------

To mark a directory and all subdirectories as an **xtask** project, simply add an **xtask.project** file in the project's root directory. This file should be in a json format and define a few configuration settings that affect the runtime behavior of **xtask**.

.. code-block:: json
	:caption: .../<project>/xtask.project

	{
		"cache_location": "cache/",
		"extension_location": "extensions/",
		"log_level": "info"
	}

cache_location
	Defines the location of the **task cache** for this project. This can be a path to any directory, even on a network drive.

extension_location
	Defines the location that should be added to the path of the process. This is useful when developing custom extensions and/or helpers to a project that should be available globally, across all taskfiles.

log_level
	Defines the log level of the application. Valid values are: "debug", "info", "warning", "error"


A Simple Taskfile
-----------------

Let's start by creating a simple taskfile that defines a group of tasks (**foo**) and a singular task (**say-hello**):

.. code-block:: python
	:caption: .../<project>/foo.tasks

	from xtask import *
	
	@task('say-hello')
	def say_hello(ctx: Context):
		print('Hello world!')

Now let's run ``xtask -h`` again:

.. code-block:: console

	.../<project>
	> xtask -h
	usage: xtask.exe [-h] {foo:say-hello,say-hello} ...

	positional arguments:
	{foo:say-hello,say-hello}
		foo:say-hello (say-hello)
			Runs the [foo:say-hello] task and all of its dependencies.

	options:
	-h, --help            show this help message and exit

Notice that the **say-hello** task we just defined is now an option on the command line.

We can run the task:

* Using its full name, **foo:say-hello**. This will run the task from anywhere in the project.
* Using its alias, **say-hello**. In this case, we can drop the group, **foo**, from the task we want to run since we are in the same directory that the task is defined.

Now let's run the task and confirm that everything works:

.. code-block:: console

	.../<project>
	> xtask say-hello
	[xtask] INFO: Preparing to execute: [xtask:say-hello]

	==================================================
	| Executing [xtask:say-hello]
	--------------------------------------------------

	Hello world!

	--------------------------------------------------
	| Successfully executed [xtask:say-hello]
	==================================================