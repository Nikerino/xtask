import logging
import typing as t
from pathlib import Path

from xtask.task import Task
from xtask.task_cache import TaskCache
from xtask.task_graph import TaskGraph
from xtask.util import working_dir


class Context():

	this_task: Task
	properties: t.Dict[str, str]

	_task_graph: TaskGraph
	_task_cache: TaskCache

	def __init__(self, this_task: Task, task_graph: TaskGraph, task_cache: TaskCache, properties: t.Dict[str, str]) -> None:
		self.this_task = this_task
		self._task_graph = task_graph
		self._task_cache = task_cache
		self.properties = properties

	def task(self, task_name: str) -> Task:
		if ':' in task_name:
			task_group, task_name = task_name.split(':')
		else:
			task_group, task_name = self.this_task.group, task_name

		for task in self._task_graph.all_tasks:
			if task.name == task_name and task.group == task_group:
				return task

		return None

	def execute(self, *tasks: Task, use_cache=True, with_dependencies=True) -> None:
		if with_dependencies:
			for task, finalizer in self._task_graph.subgraph(*tasks).topological_order():
				self._execute(task, use_cache=use_cache)
				finalizer()
		else:
			for task in tasks:
				self._execute(task, use_cache=use_cache)

	def _execute(self, task: Task, use_cache=True) -> None:
		logging.info(f'Preparing to execute: {task}')
		working_directory = str(task.working_directory_path)
		with working_dir(working_directory):
			if use_cache and self._task_cache is not None and task.use_cache:
				task_input_hash = task.input_hash()
				logging.info(f'Checking task cache for {task} with input hash {task_input_hash}')
				if task_input_hash in self._task_cache:
					logging.info(f'Found an entry for {task} with input hash {task_input_hash}')
					logging.info(f'Copying outputs cached for {task} to {working_directory}')
					self._task_cache.copy_to(task_input_hash, working_directory)
					logging.info(f'Successfully copied outputs cached for {task} to {working_directory}')
				else:
					logging.info(f'Could not find outputs in task cache for {task} with input hash {task_input_hash}')
					task._execute(self._clone_for_task(task))
					output_file_names = task.outputs()
					logging.info(f'Caching the following output files under input hash {task_input_hash}:')
					for output_file_name in output_file_names:
						logging.info(f'\t- {output_file_name}')
					self._task_cache.put(task_input_hash, [(file_name, Path(file_name).read_bytes()) for file_name in output_file_names])
					logging.info('Caching successful')
			else:
				task._execute(self._clone_for_task(task))
		
	def _clone_for_task(self, task: Task) -> 'Context':
		return Context(task, self._task_graph, self._task_cache, self.properties)