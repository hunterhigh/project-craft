from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from foundation_lib import FoundationError, generate_project, load_json, save_verification, status_text, validate_manifest, verify_project


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and verify Project Foundation starters.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate-manifest", help="Validate a schema-v1 manifest.")
    validate.add_argument("--manifest", required=True, type=Path)

    generate = subparsers.add_parser("generate", help="Generate into a new empty directory.")
    generate.add_argument("--manifest", required=True, type=Path)
    generate.add_argument("--target", required=True, type=Path)
    generate.add_argument("--run-tools", action="store_true", help="Run the adapter's local install and verification commands.")

    verify = subparsers.add_parser("verify", help="Verify a project initialized by Project Foundation.")
    verify.add_argument("--target", required=True, type=Path)
    verify.add_argument("--run-tools", action="store_true", help="Run the adapter's local verification commands.")

    status = subparsers.add_parser("status", help="Print the latest owner-oriented status.")
    status.add_argument("--target", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate-manifest":
            manifest = load_json(args.manifest.resolve())
            errors = validate_manifest(manifest)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print("Manifest is valid.")
            return 0
        if args.command == "generate":
            manifest = load_json(args.manifest.resolve())
            result = generate_project(manifest, args.target, run_tools=args.run_tools)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["status"] != "not-ready" else 2
        if args.command == "verify":
            target = args.target.resolve()
            result = verify_project(target, run_tools=args.run_tools)
            save_verification(target, result)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["status"] != "not-ready" else 2
        if args.command == "status":
            print(status_text(args.target.resolve()))
            return 0
    except FoundationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("ERROR: Interrupted", file=sys.stderr)
        return 130
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
