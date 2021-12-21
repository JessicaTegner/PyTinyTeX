import sys
import os
import re
import platform
import shutil

import zipfile
import tarfile

try:
	from urllib.request import urlopen
except ImportError:
	from urllib import urlopen


def download_tinytex(version="latest", variation=1, target_folder=".", download_folder=None):
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
	if download_folder is not None:
		if download_folder.endswith('/'):
			download_folder = download_folder[:-1]
	if download_folder is None:
		download_folder = "."
	filename = os.path.join(os.path.expanduser(download_folder), filename)
	if os.path.isfile(filename):
		print("* Using already downloaded file %s" % (filename))
	else:
		print("* Downloading TinyTeX from %s ..." % url)
		response = urlopen(url)
		with open(filename, 'wb') as out_file:
			shutil.copyfileobj(response, out_file)
		print("* Downloaded TinyTeX, saved in %s ..." % filename)
	
	print("Extracting %s to %s..." % (filename, target_folder))
	extracted_dir_name = "TinyTeX"
	if filename.endswith(".zip"):
		zf = zipfile.ZipFile(filename)
		zf.extractall(target_folder)
		zf.close()
	elif filename.endswith(".tgz"):
		tf = tarfile.open(filename, "r:gz")
		tf.extractall(target_folder)
		tf.close()
	elif filename.endswith(".tar.gz"):
		tf = tarfile.open(filename, "r:gz")
		tf.extractall(target_folder)
		tf.close()
		extracted_dir_name = ".TinyTeX"
	else:
		raise RuntimeError("File {0} not supported".format(filename))
	tinytex_extracted = os.path.join(target_folder, extracted_dir_name)
	for file_name in os.listdir(tinytex_extracted):
		shutil.move(os.path.join(tinytex_extracted, file_name), target_folder)
	shutil.rmtree(tinytex_extracted)
	print("Adding TinyTeX to path")
	sys.path.insert(0, os.path.join(target_folder, "bin"))
	print("Done")

def _get_tinytex_urls(version, variation):
	url = "https://github.com/yihui/tinytex-releases/releases/" + \
		  ("tag/" if version != "latest" else "") + version
	# read the HTML content
	response = urlopen(url)
	content = response.read()
	# regex for the binaries
	regex = re.compile(r"/yihui/tinytex-releases/releases/download/.*TinyTeX\-.*.(?:tar\.gz|tgz|zip)")
	# a list of urls to the binaries
	tinytex_urls_list = regex.findall(content.decode("utf-8"))
	# actual tinytex version
	version = tinytex_urls_list[0].split('/')[5]
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

