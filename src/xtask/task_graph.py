import graphlib
import typing as t

from xtask.task import Task
from xtask.util import *


class TaskGraph():
	
	_graph: t.Dict[Task, t.Collection[Task]]
	
	def __init__(self, tasks: t.Collection[Task]):
		graph: t.Dict[Task, t.List[Task]] = dict()
		name_and_group_to_task_map: t.Dict[t.Tuple[str, str], Task] = dict()
		for task in tasks:
			if graph.get(task) is None:
				graph[task] = list()
			name_and_group_to_task_map[(task.name, task.group)] = task
		for task in graph.keys():
			for dependency in task._unresolved_dependencies:
				if ':' in dependency:
					dep_group, dep_name = dependency.split(':')
				else:
					dep_group, dep_name = task.group, dependency
				dep_task = name_and_group_to_task_map.get((dep_name, dep_group))
				if not dep_task:
					raise RuntimeError(f'Could not find a task named "{dep_name}" in group "{dep_group}".')
				graph[task].append(dep_task)
		# We mutate the task class here, because tasks should rarely be used outside of a task graph (since dependencies would be meaningless)
		# so this is still a part of "configuring" all tasks.
		for task, deps in graph.items():
			task._dependencies = deps
		self._graph = graph
	
	@property
	def all_tasks(self) -> t.List[Task]:
		return list(self._graph.keys())
	
	def subgraph(self, *tasks: Task):
		# Use recursion to add a task then all of its dependencies to the subgraph.
		# Since doing so uses the same function, it ensures the dependencies of each dependency
		# are added to the subgraph. So on and so forth...
		task_set = set()
		def add_task_and_dependencies(task: Task):
			if task not in task_set:
				task_set.add(task)
				for dependency in task.dependencies:
					add_task_and_dependencies(dependency)
		for t in tasks:
			add_task_and_dependencies(t)
		return TaskGraph(list(task_set))

	def topological_order(self) -> None:
		sorter = graphlib.TopologicalSorter(self._graph)
		sorter.prepare()
		while sorter.is_active():
			for task in sorter.get_ready():
				yield task, lambda: sorter.done(task)