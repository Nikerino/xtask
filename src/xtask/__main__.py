import logging
import sys
from argparse import Action, ArgumentParser
from pathlib import Path

import xtask.constants as const
from xtask.context import Context
from xtask.settings import Settings
from xtask.task import Task
from xtask.task_cache import DirectoryTaskCache
from xtask.task_file import TaskFile
from xtask.task_graph import TaskGraph
from xtask.util import *

# Search upwards in directories for a root settings file. If one is not found, then just use the current directory as the root.
current_path: Path = Path.cwd()
while not (current_path / const.ROOT_SETTINGS_FILE_NAME).exists():
	if current_path == current_path.parent:
		break
	current_path = current_path.parent

if not (current_path / const.ROOT_SETTINGS_FILE_NAME).exists():
	current_path = Path.cwd()

root_project_path = current_path

settings_file_path = current_path / const.ROOT_SETTINGS_FILE_NAME
if settings_file_path.exists():
	settings = Settings.load(settings_file_path)
else:
	settings = Settings()

if settings.cache_location and Path(settings.cache_location).is_dir():
	task_cache = DirectoryTaskCache(settings.cache_location)
else:
	task_cache = None
	
if settings.extension_location and Path(settings.extension_location).is_dir():
	sys.path.insert(0, settings.extension_location)

logging.basicConfig(format='[xtask] %(levelname)s: %(message)s', level=logging._nameToLevel.get(settings.log_level.upper()))

# Create the task graph by loading the tasks from each file
search_pattern = str(Path('**', const.TASKS_FILE_PATTERN))
task_file_paths: t.List[Path] = list(root_project_path.glob(search_pattern))
tasks: t.List[Task] = list()
visited_directories = set()
for task_file_path in task_file_paths:
	logging.debug(f'Loading task file from path: "{task_file_path}"')
	task_file = TaskFile.load(task_file_path)
	if task_file_path.parent in visited_directories:
		raise RuntimeError(f'Unable to load the task file "{task_file_path}" because a task file from the same directory has already been loaded.')
	visited_directories.add(task_file_path.parent)
	tasks.extend(task_file.tasks)
	logging.debug(f'Successfully loaded a task file from "{task_file_path}" with tasks: {",".join([str(task) for task in task_file.tasks])}')

task_graph = TaskGraph(tasks)

# Build the cmd line parser
class ParseKwargs(Action):
	def __call__(self, parser, namespace, values, option_string=None):
		setattr(namespace, self.dest, dict())
		for value in values:
			key, value = value.split('=')
			getattr(namespace, self.dest)[key] = value

def main():
	parser = ArgumentParser()
	subparsers = parser.add_subparsers()

	current_working_directory_path = Path.cwd()
	tasks_in_current_dir = {task for task in tasks if task.working_directory_path == current_working_directory_path}

	for task in task_graph.all_tasks:
		if task in tasks_in_current_dir:
			aliases=[task.name]
		else:
			aliases=list()
		task_parser = subparsers.add_parser(task.label, aliases=aliases, help=f'Runs the {task} task and all of its dependencies.' if not task.doc else task.doc)
		task_parser.set_defaults(task_to_execute=task)
		task_parser.add_argument('-p', '--properties', nargs='*', type=str, action=ParseKwargs, default=dict())

	args = parser.parse_args()

	context = Context(args.task_to_execute, task_graph, task_cache, args.properties)
	context.execute(args.task_to_execute, use_cache=True, with_dependencies=True)

	exit(0)

if __name__ == '__main__':
	main()