import logging
import os
import shutil
import subprocess
import typing as t
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def working_dir(working_directory: str):
	starting_directory = os.getcwd()
	try:
		os.chdir(working_directory)
		yield
	finally:
		os.chdir(starting_directory)
		
def xglob(include: t.Iterable[str], exclude: t.Iterable[str] = list(), root_dir: str = None) -> t.List[str]:
	root_dir_path = Path(root_dir).resolve() if root_dir else Path.cwd()
	include_files = set()
	for pattern in include:
		include_files.update([str(p.resolve()) for p in root_dir_path.glob(pattern)])
	exclude_files = set()
	for pattern in exclude:
		exclude_files.update([str(p.resolve()) for p in root_dir_path.glob(pattern)])
	return list(include_files.difference(exclude_files))

def copy(src: t.Iterable[str | Path] | str | Path, dst: str | Path, keep_structure_relative_to: str | Path = None):
	def _copy(from_path: Path, to_path: Path):
		if from_path.is_file() and to_path.is_file():
			to_path.parent.mkdir(parents=True, exist_ok=True)
			to_path.unlink(missing_ok=True)
			logging.info(f'Copying "{str(file_path)}" to "{str(file_path)}"')
			shutil.copy2(str(from_path), str(to_path))
		elif from_path.is_file() and to_path.is_dir():
			_copy(from_path, to_path / from_path.name)
		elif from_path.is_dir() and to_path.is_dir():
			logging.info(f'Copying "{str(file_path)}" to "{str(file_path)}"')
			shutil.copytree(str(from_path), str(to_path), dirs_exist_ok=True)
		else:
			raise RuntimeError(f'Cannot copy "{from_path}" to "{to_path}"')

	destination_path = Path(dst).resolve()
	keep_structure_relative_to = Path(keep_structure_relative_to).resolve() if keep_structure_relative_to else None
	if isinstance(src, (t.List, t.Tuple, t.Set, t.Generator)):
		if destination_path.is_file():
			raise RuntimeError(f'Cannot copy multiple files to a single file destination: "{destination_path}"')
		for file in src:
			file_path = Path(file).resolve()
			destination_file_path = (destination_path / (file_path.relative_to(keep_structure_relative_to) if keep_structure_relative_to else file_path.name)).resolve()
			_copy(file_path, destination_file_path)
	elif isinstance(src, (str, Path)):
		file_path = Path(src).resolve()
		if file_path.is_file() and destination_path.is_dir():
			destination_file_path = (destination_path / (file_path.relative_to(keep_structure_relative_to) if keep_structure_relative_to else file_path.name)).resolve()
		else:
			# In this case, a file is being copied to a file OR a dir is being copied to a dir.
			# Thus, we cannot keep any structure since the exact paths for the copy/rename are already specified.
			if keep_structure_relative_to:
				raise RuntimeError(f'Cannot keep structure when copying and renaming a file.')
			destination_file_path = destination_path
		_copy(file_path, destination_file_path)

def move(src: t.Iterable[str | Path] | str | Path, dst: str | Path, keep_structure_relative_to: str | Path = None):
	def _move(from_path: Path, to_path: Path):
		if from_path.is_file() and to_path.is_file():
			to_path.parent.mkdir(parents=True, exist_ok=True)
			to_path.unlink(missing_ok=True)
			logging.info(f'Moving "{str(file_path)}" to "{str(file_path)}"')
			shutil.move(str(from_path), str(to_path))
		elif from_path.is_file() and to_path.is_dir():
			_move(from_path, to_path / from_path.name)
		elif from_path.is_dir() and to_path.is_dir():
			logging.info(f'Moving "{str(file_path)}" to "{str(file_path)}"')
			shutil.move(str(from_path), str(to_path), dirs_exist_ok=True)
		else:
			raise RuntimeError(f'Cannot move "{from_path}" to "{to_path}"')

	destination_path = Path(dst).resolve()
	keep_structure_relative_to = Path(keep_structure_relative_to).resolve() if keep_structure_relative_to else None
	if isinstance(src, (t.List, t.Tuple, t.Set, t.Generator)):
		if destination_path.is_file():
			raise RuntimeError(f'Cannot move multiple files to a single file destination: "{destination_path}"')
		for file in src:
			file_path = Path(file).resolve()
			destination_file_path = (destination_path / (file_path.relative_to(keep_structure_relative_to) if keep_structure_relative_to else file_path.name)).resolve()
			_move(file_path, destination_file_path)
	elif isinstance(src, (str, Path)):
		file_path = Path(src).resolve()
		if file_path.is_file() and destination_path.is_dir():
			destination_file_path = (destination_path / (file_path.relative_to(keep_structure_relative_to) if keep_structure_relative_to else file_path.name)).resolve()
		else:
			# In this case, a file is being moved to a file OR a dir is being moved to a dir.
			# Thus, we cannot keep any structure since the exact paths for the move/rename are already specified.
			if keep_structure_relative_to:
				raise RuntimeError(f'Cannot keep structure when moving and renaming a file.')
			destination_file_path = destination_path
		_move(file_path, destination_file_path)

def delete(file_or_files: t.Iterable[str | Path] | str | Path):
	if isinstance(file_or_files, (t.List, t.Tuple, t.Set, t.Generator)):
		for file in file_or_files:
			file_path = Path(file).resolve()
			if file_path.exists():
				if file_path.is_file():
					logging.info(f'Deleting "{file_path}"')
					file_path.unlink()
				else:
					logging.info(f'Deleting "{file_path}"')
					shutil.rmtree(str(file_path))
	elif isinstance(file_or_files, (str, Path)):
		file_path = Path(file_or_files).resolve()
		if file_path.exists():
			if file_path.is_file():
				logging.info(f'Deleting "{file_path}"')
				file_path.unlink()
			else:
				logging.info(f'Deleting "{file_path}"')
				shutil.rmtree(str(file_path))

def run(command_or_args: str | t.List[str], shell=True, check=True, timeout=None) -> subprocess.CompletedProcess[bytes]:
	return subprocess.run(command_or_args, shell=shell, check=check, timeout=timeout)