import logging
import os
import platform
import re
import shutil
import sys
import tarfile
import tempfile
import urllib.error
import zipfile
from pathlib import Path
from urllib.request import urlopen

logger = logging.getLogger("pytinytex")

DEFAULT_TARGET_FOLDER = Path.home() / ".pytinytex"

def _is_arm64():
	"""Return True if running on an ARM64/aarch64 machine."""
	return platform.machine().lower() in ("aarch64", "arm64")

def download_tinytex(version="latest", variation=1, target_folder=DEFAULT_TARGET_FOLDER, download_folder=None):
	if variation not in [0, 1, 2]:
		raise RuntimeError(
			"Invalid TinyTeX variation {}. Valid variations are 0, 1, 2.".format(variation)
		)
	if re.match(r"\d{4}\.\d{2}", version) or version == "latest":
		if version != "latest":
			version = "v" + version
	else:
		raise RuntimeError(
			"Invalid TinyTeX version {}. TinyTeX version has to be in the format "
			"'latest' for the latest available version, or year.month, for example: "
			"'2024.12', '2024.09' for a specific version.".format(version)
		)
	variation = str(variation)
	pf = sys.platform
	if pf.startswith("linux"):
		pf = "linux"
		if platform.architecture()[0] != "64bit":
			raise RuntimeError("Linux TinyTeX is only compiled for 64bit.")
	# get TinyTeX
	tinytex_urls, _ = _get_tinytex_urls(version, variation)
	if pf not in tinytex_urls:
		raise RuntimeError("Can't handle your platform (only Linux, Mac OS X, Windows).")
	url = tinytex_urls[pf]
	filename = url.split("/")[-1]
	if download_folder:
		download_folder = Path(download_folder)
	else:
		download_folder = Path(".")
	if target_folder:
		target_folder = Path(target_folder)
	# make sure all the folders exist
	download_folder.mkdir(parents=True, exist_ok=True)
	target_folder.mkdir(parents=True, exist_ok=True)
	filename = download_folder / filename
	if filename.exists():
		logger.info("* Using already downloaded file %s", filename)
	else:
		logger.info("* Downloading TinyTeX from %s ...", url)
		response = urlopen(url)
		with open(filename, 'wb') as out_file:
			shutil.copyfileobj(response, out_file)
		logger.info("* Downloaded TinyTeX, saved in %s ...", filename)

	logger.info("Extracting %s to a temporary folder...", filename)
	with tempfile.TemporaryDirectory() as tmpdirname:
		tmpdirname = Path(tmpdirname)
		extracted_dir_name = "TinyTeX"  # for Windows and macOS
		if filename.suffix == ".zip":
			with zipfile.ZipFile(filename) as zf:
				zf.extractall(tmpdirname)
		elif filename.suffix in (".tgz", ".gz"):
			with tarfile.open(filename, "r:gz") as tf:
				tf.extractall(tmpdirname)
			if filename.suffix == ".gz":
				extracted_dir_name = ".TinyTeX"  # linux only
		else:
			raise RuntimeError("File {0} not supported".format(filename))
		tinytex_extracted = tmpdirname / extracted_dir_name
		logger.info("Copying TinyTeX to %s...", target_folder)
		shutil.copytree(tinytex_extracted, target_folder, dirs_exist_ok=True)
	# Resolve the bin directory and add it to the OS PATH for this process
	folder_to_add_to_path = target_folder / "bin"
	while len(list(folder_to_add_to_path.glob("*"))) == 1 and folder_to_add_to_path.is_dir():
		folder_to_add_to_path = list(folder_to_add_to_path.glob("*"))[0]
	logger.info("Adding TinyTeX to PATH (%s)...", folder_to_add_to_path)
	os.environ["PATH"] = str(folder_to_add_to_path) + os.pathsep + os.environ.get("PATH", "")
	logger.info("Done")

def _get_tinytex_urls(version, variation):
	url = "https://github.com/rstudio/tinytex-releases/releases/" + \
		  ("tag/" if version != "latest" else "") + version
	try:
		response = urlopen(url)
		version_url_frags = response.url.split("/")
		version = version_url_frags[-1]
	except urllib.error.HTTPError:
		raise RuntimeError("Can't find TinyTeX version %s" % version)
	response = urlopen(
		"https://github.com/rstudio/tinytex-releases/releases/expanded_assets/" + version
	)
	content = response.read()
	regex = re.compile(
		r"/rstudio/tinytex-releases/releases/download/.*TinyTeX\-.*.(?:tar\.gz|tgz|zip)"
	)
	tinytex_urls_list = regex.findall(content.decode("utf-8"))
	ext2platform = {
		'zip': 'win32',
		'.gz': 'linux',
		'tgz': 'darwin'
	}
	if variation in ("0", "1"):
		variation_txt = "TinyTeX-{}-".format(variation)
	else:
		variation_txt = "TinyTeX-v"
	tinytex_urls_list = {
		url_frag for url_frag in tinytex_urls_list if variation_txt in url_frag
	}
	# Filter Linux tar.gz URLs by architecture: TinyTeX releases include
	# separate arm64 tarballs (e.g. "TinyTeX-0-arm64-v2026.03.02.tar.gz")
	# alongside x86_64 ones.  Both end in .tar.gz and would map to the same
	# "linux" dict key.  Only apply this filter to .tar.gz (Linux) URLs —
	# macOS .tgz and Windows .zip are unaffected.
	arm64 = _is_arm64()
	tinytex_urls_list = {
		url_frag for url_frag in tinytex_urls_list
		if not url_frag.endswith(".tar.gz") or arm64 == ("arm64" in url_frag)
	}
	tinytex_urls = {
		ext2platform[url_frag[-3:]]: ("https://github.com" + url_frag)
		for url_frag in tinytex_urls_list
	}
	return tinytex_urls, version
