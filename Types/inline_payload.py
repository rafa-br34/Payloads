#-<REV:0 VER:0.0.1
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

g_metadata = {}
g_module = sys.modules[__name__]
g_source = inspect.getsource(g_module)
g_file = pathlib.Path(inspect.getfile(g_module))


def msg(msg):
	pass

def safe_exec(fun, *args, **kwargs):
	try:
		return fun(*args, **kwargs)
	except BaseException as error:
		return error


def shell(cmd):
	return safe_exec(subprocess.check_output, cmd, shell=False)

def get_module(module):
	result = safe_exec(importlib.import_module, module)
	if isinstance(importlib, ImportError):
		return None
	else:
		return result

def get_metadata(source, table):
	for block in c_block_regex.findall(source):
		for comment in c_comment_regex.findall(block):
			for name, value in c_metadata_regex.findall(comment):
				table[name] = value
	
	return table


get_metadata(g_source, g_metadata)

msg("Checking dependencies")
for dep in c_dependencies:
	msg(f"\tLoading: {dep}")

	if get_module(dep) == None:
		msg(shell(f"{sys.executable} -m pip install {dep}"))

	globals()[dep] = get_module(dep)

current_revision = int(g_metadata["REV"])
newest_revision = int(g_metadata["REV"])
newest_source = None

for source in c_sources:
	msg(f"Checking {source}")
	for i in range(3):
		try:
			raw_code = requests.get(source).text
			metadata = get_metadata(raw_code, {})

			if int(metadata["REV"]) > newest_revision:
				newest_revision = int(metadata["REV"])
				newest_source = raw_code
		except BaseException as error:
			msg(f"\tAttempt {i + 1} failed, {type(error).__name__}")
		else:
			break


if newest_source:
	msg(f"Trying to update from revision {current_revision} to {newest_revision}")
	try:
		g_file.write_text(c_block_regex.sub(newest_source.replace('\r', '').replace("\\", "\\\\"), g_file.read_text(), re.MULTILINE))
	except BaseException as error:
		msg(error)

for name, value in g_metadata.items():
	msg(f"{name}: {value}")
#>-