#-<REV:1 VER:0.0.1


def __entry():
	import multiprocessing
	import subprocess
	import importlib
	import inspect
	import pathlib
	import sys
	import re

	c_dependencies = ["requests"]
	c_sources = []

	c_metadata_regex = re.compile(r"(\w+):.*?(\S+)")
	c_comment_regex = re.compile(r"\#.*")
	c_block_regex = re.compile(r"#\s*-<[\s\S]*#\s*>-")
	c_venv_name = ".py-venv"

	g_metadata = {}
	g_module = sys.modules[__name__]
	g_source = inspect.getsource(g_module)
	g_file = pathlib.Path(inspect.getfile(g_module))

	g_venv_path = g_file.parent.joinpath(c_venv_name)
	g_venv_path_abs = g_venv_path.absolute()
	g_venv_path_python = f"{g_venv_path_abs}/bin/python"
	g_venv_exists = g_venv_path.exists()
	g_venv_enabled = sys.executable == g_venv_path_python

	def msg(val):
		pass

	def safe_exec(procedure, *args, **kwargs):
		try:
			return procedure(*args, **kwargs)
		except Exception as error:
			return error

	def shell(cmd):
		return safe_exec(
			subprocess.check_output,
			cmd.split(),
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
		for block in c_block_regex.findall(source):
			for comment in c_comment_regex.findall(block):
				for name, value in c_metadata_regex.findall(comment):
					table[name] = value

		return table

	def core_routine():
		nonlocal g_venv_enabled, g_venv_exists

		if not g_venv_enabled and not g_venv_exists:
			result = shell(f"{sys.executable} -m venv {g_venv_path_abs}")

			if isinstance(result, subprocess.CalledProcessError):
				msg(f"Failed to create venv: {result} {result.__dict__}")
			else:
				g_venv_exists = True

		if g_venv_exists and not g_venv_enabled:
			msg(f"Starting new instance with venv at {g_venv_path_abs}")
			result = shell(f"{g_venv_path_python} {g_file.absolute()}")
			result = isinstance(result, bytes) and result.decode() or ""
			msg(f"Result: {result}")
			return

		get_metadata(g_source, g_metadata)

		if g_venv_exists:
			install_fmt = f"{g_venv_path_abs}/bin/pip install {{}}"
		else:
			install_fmt = f"{sys.executable} -m pip install {{}}"

		msg("Installing dependencies")
		for dep in c_dependencies:
			if get_module(dep):
				msg(f"\tSkipping: {dep}")
				continue

			msg(f"\tInstalling: {dep}")
			result = shell(install_fmt.format(dep))

			if not isinstance(result, subprocess.CalledProcessError):
				msg(f"\t{dep}: {result}")
			elif b"externally-managed-environment" in result.stderr:
				msg(f"\t{dep}: Environment issue {result} {result.__dict__}")
			else:
				msg(f"\t{dep}: Install issue {result} {result.__dict__}")

		module_dict = {}

		msg("Loading dependencies")
		for dep in c_dependencies:
			result = get_module(dep)

			msg(f"\t{dep}: {result}")
			module_dict[dep] = result

		current_revision = int(g_metadata["REV"])
		newest_revision = int(g_metadata["REV"])
		newest_source = None

		for source in c_sources:
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
				g_file.write_text(
					c_block_regex.sub(
						newest_source.replace('\r', '').replace("\\", "\\\\"),
						g_file.read_text(),
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

		import time

		while True:
			msg("Heartbeat")
			time.sleep(5)

	if not g_venv_enabled:
		__proc = multiprocessing.Process(target = core_routine)
		__proc.start()
	else:
		core_routine()


__entry()
#>-
