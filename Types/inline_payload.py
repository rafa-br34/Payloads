#-<REV:1 VER:0.0.1


def __entry():
	import subprocess
	import importlib
	import threading
	import inspect
	import pathlib
	import sys
	import os
	import re

	CFG_DEPENDENCIES = ["requests"]
	CFG_VENV_NAME = ".py-venv"
	CFG_SOURCES = []

	REGEX_METADATA = re.compile(r"(\w+):.*?(\S+)")
	REGEX_COMMENT = re.compile(r"\#.*")
	REGEX_BLOCK = re.compile(r"#\s*-<[\s\S]*#\s*>-")

	SELF_MODULE = sys.modules[__name__]
	SELF_SOURCE = inspect.getsource(SELF_MODULE)
	SELF_PATH = pathlib.Path(inspect.getfile(SELF_MODULE))
	SELF_CURR_DIR = pathlib.Path.cwd()

	VENV_PATH = SELF_CURR_DIR.joinpath(CFG_VENV_NAME)
	VENV_PATH_REL = CFG_VENV_NAME

	if os.name == "nt":
		VENV_PATH_PYTHON = f"{VENV_PATH_REL}/Scripts/python.exe"
	else:
		VENV_PATH_PYTHON = f"{VENV_PATH_REL}/bin/python"

	VENV_ENABLED = pathlib.Path(sys.executable) == SELF_CURR_DIR.joinpath(VENV_PATH_PYTHON)

	g_metadata = {}
	g_venv_exists = VENV_PATH.exists()

	def msg(val):
		pass

	msg(f"{VENV_ENABLED} {pathlib.Path(sys.executable)} {SELF_CURR_DIR.joinpath(VENV_PATH_PYTHON)}")

	def safe_exec(procedure, *args, **kwargs):
		try:
			return procedure(*args, **kwargs)
		except Exception as error:
			return error

	def shell(cmd):
		return safe_exec(
			subprocess.check_output,
			cmd,
			stderr = subprocess.PIPE,
			shell = False,
		)

	def get_module(module):
		result = safe_exec(importlib.import_module, module)
		if isinstance(result, ImportError):
			return None
		else:
			return result

	def get_metadata(source, table):
		for block in REGEX_BLOCK.findall(source):
			for comment in REGEX_COMMENT.findall(block):
				for name, value in REGEX_METADATA.findall(comment):
					table[name] = value

		return table

	def prepare_environment():
		nonlocal g_venv_exists

		if not VENV_ENABLED and not g_venv_exists:
			result = shell([sys.executable, "-m", "venv", VENV_PATH_REL])

			if isinstance(result, subprocess.CalledProcessError):
				msg(f"Failed to create venv: {result} {result.__dict__}")
			else:
				msg(f"Created venv at {VENV_PATH_REL}")
				g_venv_exists = True

	def core_routine():
		prepare_environment()

		msg(f"{sys.executable} {VENV_PATH_PYTHON}")
		if g_venv_exists and not VENV_ENABLED:
			msg(f"Starting new instance with venv at {VENV_PATH_REL}")

			result = safe_exec(
				subprocess.Popen,
				[VENV_PATH_PYTHON, SELF_PATH.absolute()],
				stdout = subprocess.DEVNULL,
				stderr = subprocess.DEVNULL,
				start_new_session = False,
			)

			if not isinstance(result, subprocess.Popen):
				msg(f"Failed: {result}")
			else:
				status = result.poll()
				if status is None:
					msg("Running")
				else:
					msg(f"Returned status: {status}")

			return

		if g_venv_exists:
			python_bin = VENV_PATH_PYTHON
		else:
			python_bin = sys.executable

		msg("Installing dependencies")
		for dep in CFG_DEPENDENCIES:
			if get_module(dep):
				msg(f"\tSkipping: {dep}")
				continue

			msg(f"\tInstalling: {dep}")
			result = shell([python_bin, "-m", "pip", "install", dep])

			if not isinstance(result, subprocess.CalledProcessError):
				msg(f"\t{dep}: {result}")
			elif b"externally-managed-environment" in result.stderr:
				msg(f"\t{dep}: Environment issue {result} {result.__dict__}")
			else:
				msg(f"\t{dep}: Install issue {result} {result.__dict__}")

		get_metadata(SELF_SOURCE, g_metadata)

		module_dict = {}

		msg("Loading dependencies")
		for dep in CFG_DEPENDENCIES:
			result = get_module(dep)

			msg(f"\t{dep}: {result}")
			module_dict[dep] = result

		current_revision = int(g_metadata["REV"])
		newest_revision = int(g_metadata["REV"])
		newest_source = None

		for source in CFG_SOURCES:
			msg(f"Checking {source}")
			for i in range(3):
				try:
					raw_code = module_dict["requests"].get(source).text
					metadata = get_metadata(raw_code, {})

					if int(metadata["REV"]) > newest_revision:
						newest_revision = int(metadata["REV"])
						newest_source = raw_code
				except Exception as error:
					msg(f"\tAttempt {i + 1} failed, {type(error).__name__}")
				else:
					break

		if newest_source:
			msg(f"Trying to update from revision {current_revision} to {newest_revision}")
			try:
				SELF_PATH.write_text(
					REGEX_BLOCK.sub(
						newest_source.replace('\r', '').replace("\\", "\\\\"),
						SELF_PATH.read_text(),
						re.MULTILINE,
					)
				)
			except Exception as error:
				msg(error)

		for name, value in g_metadata.items():
			msg(f"{name}: {value}")

		payload(module_dict)

	def payload(module_dict):
		for key, val in module_dict.items():
			locals()[key] = val

		main_thread = threading.main_thread()
		import time

		while main_thread.is_alive():
			msg("Heartbeat")
			time.sleep(5)

		main_thread.join()

	if not VENV_ENABLED:
		__thread = threading.Thread(target = core_routine)
		__thread.start()
	else:
		core_routine()


__entry()
#>-
