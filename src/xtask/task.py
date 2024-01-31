import hashlib
import inspect
import logging
import struct
import sys
import traceback
import typing as t
from pathlib import Path

import colorama

import xtask.constants as const
from xtask.util import *

if t.TYPE_CHECKING:
	from xtask.context import Context

class Task():
	name: str
	group: str
	doc: str
	working_directory_path: Path
	use_cache: bool
	file_path: Path

	_unresolved_dependencies: t.List[str]
	_dependencies: t.List[str]
	_additional_inputs: t.List[bytes]
	_include_src_patterns: t.List[str]
	_exclude_src_patterns: t.List[str]
	_include_out_patterns: t.List[str]
	_exclude_out_patterns: t.List[str]
	_action: t.Callable

	def __init__(self, 
				name: str,
				group: str,
				doc: str,
				working_directory_path: Path,
				use_cache: bool,
				action: t.Callable[['Context'], None],
				file_path: int):
		self.name = name
		self.group = group
		self.doc = doc
		self.working_directory_path = working_directory_path
		self.file_path = file_path
		self.use_cache = use_cache
		self._unresolved_dependencies = list()
		self._dependencies = None
		self._additional_inputs = list()
		self._include_src_patterns = list()
		self._exclude_src_patterns = list()
		self._include_out_patterns = list()
		self._exclude_out_patterns = list()
		self._action = action

	@property
	def label(self):
		return f'{self.group}:{self.name}'
	
	@property
	def dependencies(self) -> t.List['Task']:
		if self._dependencies is None:
			raise RuntimeError(f'Cannot access the dependencies of this task, {self}, before it is finished being configured.')
		return self._dependencies

	def inputs(self) -> t.List[str]:
		return xglob(include=self._include_src_patterns, exclude=self._exclude_src_patterns, root_dir=str(self.working_directory_path))

	def outputs(self) -> t.List[str]:
		return xglob(include=self._include_out_patterns, exclude=self._exclude_out_patterns, root_dir=str(self.working_directory_path))
	
	def copy_outputs(self, destination_directory: str | Path, include: str = '*', exclude: str = '', keep_structure: bool = False):
		files_to_copy = list()
		for file in self.outputs():
			file_path = Path(file).resolve()
			if file_path.match(include) and not (file_path.match(exclude) if exclude else False):
				files_to_copy.append(file_path)
		copy(files_to_copy, destination_directory, keep_structure_relative_to=(self.working_directory_path if keep_structure else None))

	def input_hash(self) -> int:
		logging.debug(f'Hashing inputs for {self}')
		in_hash = hashlib.md5()

		logging.debug(f'Updating with file hash {self.file_path}')
		in_hash.update(self.file_path.read_bytes())

		logging.debug(f'Updating hash with files:')
		for input_file in sorted(self.inputs()):
			logging.debug(f'\t- "{input_file}"')
			in_hash.update(Path(input_file).read_bytes())

		logging.debug('Updating hash with additionl inputs')
		for additional_input in self._additional_inputs:
			in_hash.update(additional_input)

		return int.from_bytes(in_hash.digest(), byteorder=sys.byteorder)
	
	def _execute(self, ctx: 'Context') -> None:
		try:
			print(colorama.Style.BRIGHT + colorama.Fore.CYAN)
			print('==================================================')
			print(f'| Executing {self}')
			print('--------------------------------------------------')
			print(colorama.Style.RESET_ALL)
			self._action(ctx)
			print(colorama.Style.BRIGHT + colorama.Fore.GREEN)
			print('--------------------------------------------------')
			print(f'| Successfully executed {self}')
			print('==================================================')
			print(colorama.Style.RESET_ALL)
		except Exception:
			traceback.print_exc()
			print(colorama.Style.BRIGHT + colorama.Fore.RED)
			print('--------------------------------------------------')
			print(f'| Failed to execute {self}')
			print('==================================================')
			print(colorama.Style.RESET_ALL)


	def __hash__(self) -> int:
		return hash((self.name, self.group))

	def __eq__(self, __value: object) -> bool:
		return isinstance(__value, Task) and self.name == __value.name and self.group == __value.group

	def __ne__(self, __value: object) -> bool:
		return not (self == __value)
	
	def __str__(self) -> str:
		return f'[{self.label}]'
	
	def __repr__(self) -> str:
		return f'[{self.label}]'

def task(name: str, use_cache: bool = False) -> t.Callable[..., Task]:
	def inner(func):
		# Gets the most recent *.tasks file in the call stack, which should be the task file we are meant to be defined in.
		# Tasks can be defined inside of functions and inside *.py files that may be imported from anywhere. Thus, we look back
		# until we find the *.tasks file that originally called a function to define a task so we can obtain our group name and
		# working directory. Because task files should not be imported (only loaded with a TaskFile instance), there should never
		# be two task files on the callstack.
		try:
			frame_info = next(iter([frame_info for frame_info in inspect.stack() if frame_info.filename.endswith(const.TASKS_FILE_EXTENSION)]))
		except StopIteration:
			raise RuntimeError(f'Cannot define the task "{name}" because a corresponding task file cannot be found.')
		frame = frame_info.frame
		file_path = Path(frame_info.filename).resolve()
		dir_path = file_path.parent
		task_doc = inspect.getdoc(func)
		
		# This assumes these attributes have already been set, which happens when a TaskFile instance loads the taskfile defining this task.
		# If these are not set, raise an error.
		all_tasks: t.List[Task] = frame.f_globals.get(const.ALL_TASKS_ATTR)
		group: str = frame.f_globals.get(const.GROUP_NAME_ATTR)
		if all_tasks is None or group is None:
			raise RuntimeError('Cannot define task because the task file was not initialized properly. Task files cannot be imported.')

		new_task = Task(name=name, 
				  		group=group,
						doc=task_doc, 
						working_directory_path=dir_path, 
						use_cache=use_cache, 
						action=func,
						file_path=file_path)

		all_tasks.append(new_task)
		return new_task
	return inner

def additional_inputs(*additional_inputs: t.Any):
	def inner(task: Task):
		for additional_input in additional_inputs:
			if isinstance(additional_input, bytes):
				task._additional_inputs.append(additional_input)
			if isinstance(additional_input, int):
				# Use some math to determine the number of bytes needed to represent this integer, then convert it
				# to bytes using that many bytes. Always use little endian and store as signed.
				task._additional_inputs.append(additional_input.to_bytes((additional_input.bit_length() + 7) // 8, 'little', signed=True))
			elif isinstance(additional_input, float):
				# If argument is a float (64-bit double precision under the hood), pack as a double.
				task._additional_inputs.append(struct.pack('d', additional_input))
			else:
				# If the argument is not int or float, then try and convert it into a string to encode it.
				try:
					additional_input_str = str(additional_input)
				except:
					raise RuntimeError(f'Error configuring inputs for {task}. Unable to encode as bytes.')
				task._additional_inputs.append(additional_input_str.encode(encoding='utf-8'))
		return task
	return inner


def inputs(include: t.Iterable[str] = None, exclude: t.Iterable[str] = None):
	if not include:
		raise RuntimeError('Unable to configure outputs for a task if no patterns were specified.')

	def inner(task: Task):
		if include:
			task._include_src_patterns.extend(include)
		if exclude:
			task._exclude_src_patterns.extend(exclude)
		return task
	return inner

def outputs(include: t.Iterable[str] = None, exclude: t.Iterable[str] = None):
	if not include:
		raise RuntimeError('Unable to configure outputs for a task if no patterns were specified.')
	
	def inner(task: Task):
		task._include_out_patterns.extend(include)
		if exclude:
			task._exclude_out_patterns.extend(exclude)
		return task
	return inner

def dependencies(*tasks):
	def inner(task: Task):
		task._unresolved_dependencies.extend(tasks)
		return task
	return inner