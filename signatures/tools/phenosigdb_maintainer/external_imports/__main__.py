from __future__ import annotations

import argparse
import json

from .registry import list_resources, run_importers
from ..resource_build import package_runtime_resource


def main() -> None:
    parser = argparse.ArgumentParser(description="Internal external-resource importer for PhenoSigDB")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List available external resource importers")

    run_parser = subparsers.add_parser("run", help="Run one or more external resource importers")
    run_parser.add_argument("resources", nargs="+", help="Importer names")
    run_parser.add_argument("--force", action="store_true", help="Redownload raw files and rebuild outputs")
    run_parser.add_argument("--output-root", default=None, help="Override output root directory")

    package_parser = subparsers.add_parser("runtime-package", help="Build a runtime cache artifact from a staged resource import")
    package_parser.add_argument("resource", choices=["celltypist", "cellmarker"], help="Runtime resource name")
    package_parser.add_argument("archive_path", help="Output .tar.gz archive path")
    package_parser.add_argument("--staging-root", default=None, help="Override staged import directory")

    args = parser.parse_args()

    if args.command == "list":
        for name in list_resources():
            print(name)
        return

    if args.command == "runtime-package":
        archive_path = package_runtime_resource(args.resource, args.archive_path, staging_root=args.staging_root)
        print(json.dumps({"resource": args.resource, "archive_path": str(archive_path)}, indent=2))
        return

    manifests = run_importers(args.resources, output_root=args.output_root, force=args.force)
    print(json.dumps(manifests, indent=2))


if __name__ == "__main__":
    main()
