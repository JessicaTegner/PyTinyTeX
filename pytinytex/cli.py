"""Command-line interface for pytinytex."""

from __future__ import annotations

import argparse
import sys


def main(argv=None):
	"""Entry point for ``python -m pytinytex``."""
	parser = argparse.ArgumentParser(
		prog="pytinytex",
		description="Manage TinyTeX installations and compile LaTeX documents.",
	)
	sub = parser.add_subparsers(dest="command")

	# compile
	p_compile = sub.add_parser("compile", help="Compile a .tex file to PDF")
	p_compile.add_argument("file", help="Path to the .tex file")
	p_compile.add_argument("--engine", default="pdflatex",
		choices=["pdflatex", "xelatex", "lualatex", "latex"],
		help="LaTeX engine (default: pdflatex)")
	p_compile.add_argument("--output-dir", default=None,
		help="Output directory for generated files")
	p_compile.add_argument("--runs", type=int, default=1,
		help="Number of compilation passes (default: 1)")
	p_compile.add_argument("--auto-install", action="store_true",
		help="Automatically install missing packages")
	p_compile.add_argument("--extra-args", nargs="*", default=None,
		help="Extra arguments to pass to the engine")

	# install
	p_install = sub.add_parser("install", help="Install a TeX Live package")
	p_install.add_argument("package", help="Package name to install")

	# remove
	p_remove = sub.add_parser("remove", help="Remove a TeX Live package")
	p_remove.add_argument("package", help="Package name to remove")

	# list
	sub.add_parser("list", help="List installed packages")

	# search
	p_search = sub.add_parser("search", help="Search for packages")
	p_search.add_argument("query", help="Search query")

	# info
	p_info = sub.add_parser("info", help="Show package information")
	p_info.add_argument("package", help="Package name")

	# update
	p_update = sub.add_parser("update", help="Update packages")
	p_update.add_argument("package", nargs="?", default="-all",
		help="Package to update (default: all)")

	# version
	sub.add_parser("version", help="Show TinyTeX/TeX Live version")

	# doctor
	sub.add_parser("doctor", help="Check TinyTeX installation health")

	# download
	p_download = sub.add_parser("download", help="Download TinyTeX")
	p_download.add_argument("--variation", type=int, default=1,
		choices=[0, 1, 2], help="TinyTeX variation (default: 1)")
	p_download.add_argument("--version", default="latest",
		help="TinyTeX version (default: latest)")

	# uninstall
	p_uninstall = sub.add_parser("uninstall", help="Remove TinyTeX installation")
	p_uninstall.add_argument("--path", default=None,
		help="Path to TinyTeX installation to remove")

	args = parser.parse_args(argv)

	if not args.command:
		parser.print_help()
		return 1

	import pytinytex

	try:
		if args.command == "compile":
			result = pytinytex.compile(
				args.file,
				engine=args.engine,
				output_dir=args.output_dir,
				num_runs=args.runs,
				auto_install=args.auto_install,
				extra_args=args.extra_args,
			)
			if result.installed_packages:
				print("Auto-installed packages: " + ", ".join(result.installed_packages))
			if result.errors:
				print("Errors:")
				for entry in result.errors:
					loc = ""
					if entry.file:
						loc += entry.file
					if entry.line:
						loc += ":" + str(entry.line)
					if loc:
						loc = " (" + loc + ")"
					print("  ! " + entry.message + loc)
			if result.warnings:
				print("Warnings: %d" % len(result.warnings))
			if result.success:
				print("Success: " + str(result.pdf_path))
			else:
				print("Compilation failed.")
				return 1

		elif args.command == "install":
			exit_code, output = pytinytex.install(args.package)
			if output:
				print(output)

		elif args.command == "remove":
			exit_code, output = pytinytex.remove(args.package)
			if output:
				print(output)

		elif args.command == "list":
			packages = pytinytex.list_installed()
			for pkg in packages:
				marker = "i" if pkg.get("installed") else " "
				detail = pkg.get("detail", "")
				print(" %s %s  %s" % (marker, pkg["name"], detail))

		elif args.command == "search":
			results = pytinytex.search(args.query)
			for pkg in results:
				desc = pkg.get("description", pkg.get("detail", ""))
				print("  %s  %s" % (pkg["name"], desc))

		elif args.command == "info":
			info = pytinytex.info(args.package)
			for key, value in info.items():
				print("  %s: %s" % (key, value))

		elif args.command == "update":
			exit_code, output = pytinytex.update(args.package)
			if output:
				print(output)

		elif args.command == "version":
			print(pytinytex.get_version())

		elif args.command == "doctor":
			result = pytinytex.doctor()
			for check in result.checks:
				status = "PASS" if check.passed else "FAIL"
				print("  [%s] %s: %s" % (status, check.name, check.message))
			if result.healthy:
				print("\nAll checks passed.")
			else:
				print("\nSome checks failed.")
				return 1

		elif args.command == "download":
			pytinytex.download_tinytex(
				version=getattr(args, "version", "latest"),
				variation=args.variation,
			)
			print("Done.")

		elif args.command == "uninstall":
			pytinytex.uninstall(args.path)
			print("TinyTeX uninstalled.")

	except RuntimeError as e:
		print("Error: %s" % e, file=sys.stderr)
		return 1

	return 0
