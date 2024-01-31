import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings():
	
	cache_location: str = None
	extension_location: str = None
	log_level: str = 'info'

	@classmethod
	def load(cls, file_path: Path) -> 'Settings':
		config = json.loads(file_path.read_text())
		return Settings(**config)
