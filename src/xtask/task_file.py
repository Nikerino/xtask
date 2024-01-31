import os
import typing as t
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path

import xtask.constants as const
from xtask.task import Task


class TaskFile():

	file_path: Path
	tasks: t.List[Task]
	group_name: str

	def __init__(self, file_path: Path, tasks: t.List[Task], group: str):
		self.file_path = file_path
		self.tasks = tasks
		self.group = group

	@staticmethod
	def load(task_file: str | Path):
		task_file_path: Path = Path(task_file).resolve()
		if not task_file.is_file():
			raise RuntimeError(f'Could not load the task file "{task_file_path}" because it is not a file.')

		# By default, the group name is the name of the file before the ".tasks" extension.
		group_name = task_file_path.name.split(os.extsep)[0]

		# First create a spec from a source file, then create a module object from the spec. Use the SourceFileLoader because the task file does not have
		# the conventional .py extension.
		spec = spec_from_loader(group_name, SourceFileLoader(group_name, str(task_file_path)))
		module = module_from_spec(spec)

		# Set these attributes so that any tasks being defined in the file can add to them when executed, which can then be stored
		# in an instance of this class.
		setattr(module, const.ALL_TASKS_ATTR, list())
		setattr(module, const.GROUP_NAME_ATTR, group_name)

		# Execute the module, which will define all tasks inside, adding them to the __all_tasks__ global attribute. Read the group name in case the user
		# wants to explicitely set a different group name.
		spec.loader.exec_module(module)
		module_tasks = getattr(module, const.ALL_TASKS_ATTR)
		module_group = getattr(module, const.GROUP_NAME_ATTR)

		return TaskFile(task_file_path, module_tasks, module_group)
