import os
import sys

import re
import platform
import shutil
import urllib
import zipfile
import tarfile
from pathlib import Path
import tempfile

try:
	from urllib.request import urlopen
except ImportError:
	from urllib import urlopen

DEFAULT_TARGET_FOLDER = Path.home() / ".pytinytex"

def download_tinytex(version="latest", variation=1, target_folder=DEFAULT_TARGET_FOLDER, download_folder=None):
	if variation not in [0, 1, 2]:
		raise RuntimeError("Invalid TinyTeX variation {}. Valid variations are 0, 1, 2.".format(variation))
	if re.match(r"\d{4}\.\d{2}", version) or version == "latest":
		if version != "latest":
			version = "v" + version
	else:
		raise RuntimeError("Invalid TinyTeX version {}. TinyTeX version has to be in the format 'latest' for the latest available version, or year.month, for example: '2024.12', '2024.09' for a specific version.".format(version))
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
		print("* Using already downloaded file %s" % (str(filename)))
	else:
		print("* Downloading TinyTeX from %s ..." % url)
		response = urlopen(url)
		with open(filename, 'wb') as out_file:
			shutil.copyfileobj(response, out_file)
		print("* Downloaded TinyTeX, saved in %s ..." % filename)
	
	print("Extracting %s to a temporary folder..." % filename)
	with tempfile.TemporaryDirectory() as tmpdirname:
		tmpdirname = Path(tmpdirname)
		extracted_dir_name = "TinyTeX" # for Windows and MacOS
		if filename.suffix == ".zip":
			zf = zipfile.ZipFile(filename)
			zf.extractall(tmpdirname)
			zf.close()
		elif filename.suffix == ".tgz":
			tf = tarfile.open(filename, "r:gz")
			tf.extractall(tmpdirname)
			tf.close()
		elif filename.suffix == ".gz":
			tf = tarfile.open(filename, "r:gz")
			tf.extractall(tmpdirname)
			tf.close()
			extracted_dir_name = ".TinyTeX" # for linux only
		else:
			raise RuntimeError("File {0} not supported".format(filename))
		tinytex_extracted = tmpdirname / extracted_dir_name
		# copy the extracted folder to the target folder, overwriting if necessary
		print("Copying TinyTeX to %s..." % target_folder)
		shutil.copytree(tinytex_extracted, target_folder, dirs_exist_ok=True)
	# go into target_folder/bin, and as long as we keep having 1 and only 1 subfolder, go into that, and add it to path
	folder_to_add_to_path = target_folder / "bin"
	while len(list(folder_to_add_to_path.glob("*"))) == 1 and folder_to_add_to_path.is_dir():
		folder_to_add_to_path = list(folder_to_add_to_path.glob("*"))[0]
	print(f"Adding TinyTeX to path ({str(folder_to_add_to_path)})...")
	sys.path.append(str(folder_to_add_to_path))
	os.environ["PYTINYTEX_TINYTEX"] = str(folder_to_add_to_path)
	print("Done")

def _get_tinytex_urls(version, variation):
	url = "https://github.com/rstudio/tinytex-releases/releases/" + \
		  ("tag/" if version != "latest" else "") + version
	# try to open the url
	try:
		response = urlopen(url)
		version_url_frags = response.url.split("/")
		version = version_url_frags[-1]
	except urllib.error.HTTPError:
		raise RuntimeError("Can't find TinyTeX version %s" % version)
	# read the HTML content
	response = urlopen("https://github.com/rstudio/tinytex-releases/releases/expanded_assets/"+version)
	content = response.read()
	# regex for the binaries
	regex = re.compile(r"/rstudio/tinytex-releases/releases/download/.*TinyTeX\-.*.(?:tar\.gz|tgz|zip)")
	# a list of urls to the binaries
	tinytex_urls_list = regex.findall(content.decode("utf-8"))
	# dict that lookup the platform from binary extension
	ext2platform = {
		'zip': 'win32',
		'.gz': 'linux',
		'tgz': 'darwin'
	}
	# parse tinytex from list to dict
	variation_txt = ""
	if variation == "0" or variation == "1":
		variation_txt = "TinyTeX-{}-".format(variation)
	else:
		variation_txt = "TinyTeX-v"
	tinytex_urls_list = {url_frag for url_frag in tinytex_urls_list if variation_txt in url_frag}
	tinytex_urls = {ext2platform[url_frag[-3:]]: ("https://github.com" + url_frag) for url_frag in tinytex_urls_list}
	return tinytex_urls, version

