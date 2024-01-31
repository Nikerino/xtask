Learn
=====

Tasks
-----

Tasks are the heart of **xtask** (shocking). Simply put, a task:

.. hlist::
	:columns: 2

	* Has a name
	* Has a group
	* Has a working directory
	* Can have dependencies
	* Can have inputs
	* Can have outputs
	* Can have additional command-line options
	* Has an action

Task names and groups
	All tasks must be strongly named via a **name** and **group**. Two tasks can have the same **name** as long as their **group** is different. Two tasks within the same **group** cannot share the same **name**. A tasks full name can be represented as "<group>:<name>" - e.g. for a task named *foo* in group *bar*, the task's full name would be *bar:foo*.

	The group for a task is set to the name of the *.tasks* file (without the extension) that the task was defined in.

Task working directory
	A tasks working directory is the same as the directory it was defined in. Any paths or commands run inside the task will be relative to this working directory.

Task dependencies
	Tasks can depend on other tasks. This relationship is used during the construction of the dependency graph to ensure that a task will only ever execute after its dependencies have also been executed.

Task inputs
	Tasks can define what input files affect the execution behavior of themselves. This feature is particularly useful for **task caching**.
	
	At runtime, these inputs are hashed to create a task's **input hash**. If the task is configured to use caching, then when run, it will first check the **task cache** to see if this input hash has previously been built. If it has been built before, we copy the output files matching the task's input hash to the task's working directory. 

Task outputs
	...

Task options
	...

Task action
	Each task corresponds to an **action**. An **action** quite literally *is* a python function.

	This function always accepts a **Context** instance, which supplies a reference to the current task, and some utility for finding and executing other tasks. 
	
	The task's **action** will always execute in the task's working directory.