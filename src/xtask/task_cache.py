import abc
import typing as t
from pathlib import Path
from zipfile import ZipFile


class TaskCache(abc.ABC):

    @abc.abstractmethod
    def get(self, input_hash: int) -> t.List[t.Tuple[str, bytes]]: ...
    
    @abc.abstractmethod
    def copy_to(self, input_hash: int, target_dir: str) -> None: ...
    
    @abc.abstractmethod
    def put(self, input_hash: int, files: t.List[t.Tuple[str, bytes]]) -> None: ...
    
    @abc.abstractmethod
    def __contains__(self, input_hash: int) -> bool: ...
        
class DirectoryTaskCache(TaskCache):
    
    _directory_path: Path
    
    def __init__(self, directory_path: str):
        self._directory_path = Path(directory_path)
    
    def __contains__(self, input_hash: int) -> bool:
        cache_file = Path(self._directory_path, str(input_hash))
        return cache_file.exists()
    
    def get(self, input_hash: int) -> t.Optional[t.List[t.Tuple[str, bytes]]]:
        cache_file = Path(self._directory_path, str(input_hash))
        files = list()
        if cache_file.exists():
            with ZipFile(str(cache_file.resolve()), 'r') as zip_file:
                for file in zip_file.filelist:
                    files.append((file.filename, zip_file.read(file)))
            return files
        else:
            return None
        
    def copy_to(self, input_hash: int, target_dir: str) -> None:
        cache_file = Path(self._directory_path, str(input_hash))
        if cache_file.exists():
            with ZipFile(str(cache_file.resolve()), 'r') as zip_file:
                zip_file.extractall(target_dir)
    
    def put(self, input_hash: int, files: t.List[t.Tuple[str, bytes]]) -> None:
        with ZipFile(str(Path(self._directory_path, str(input_hash)).resolve()), 'w') as zip_file:
            for file_path, file_content in files:
                zip_file.writestr(file_path, file_content)