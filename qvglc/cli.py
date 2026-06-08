from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from qvglc.conformance import run_conformance_checks
from qvglc.coverage import coverage_report
from qvglc.emit_lvgl import EmitError, emit_module
from qvglc.emit_lvgl.conf import merge_sdkconfig_fragment
from qvglc.parser import QvglDiagnostic, check_qml, compile_qml, default_profile_path, load_profile
from qvglc.ir import (
    decode_binary,
    encode_module,
    load_json_path,
    module_to_dict,
    validate,
)
from qvglc.lvgl_probe import probe_lvgl
from qvglc.run_preview import run_qml_preview


def _load_module(path: Path):
    if path.suffix == ".json" or path.name.endswith(".qvglir.json"):
        return load_json_path(path)
    return decode_binary(path.read_bytes())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qvglc", description="QVGL QML-to-LVGL compiler")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ir = sub.add_parser("ir", help="Convert JSON IR dump to binary .qvglir")
    p_ir.add_argument("input", type=Path, help="Input .qvglir.json")
    p_ir.add_argument("-o", "--output", type=Path, required=True, help="Output .qvglir")

    p_dump = sub.add_parser("dump", help="Dump binary .qvglir to JSON")
    p_dump.add_argument("input", type=Path, help="Input .qvglir")
    p_dump.add_argument("--json", action="store_true", help="Print JSON (default)")

    p_validate = sub.add_parser("validate", help="Validate JSON IR")
    p_validate.add_argument("input", type=Path)

    p_emit = sub.add_parser("emit", help="Emit LVGL C sources from IR")
    p_emit.add_argument("input", type=Path, help="Input .qvglir or .qvglir.json")
    p_emit.add_argument("-o", "--output", type=Path, required=True, help="Output directory")
    p_emit.add_argument(
        "--lvgl-path",
        type=Path,
        default=Path("../lvgl"),
        help="LVGL source tree for capability probe",
    )

    p_compile = sub.add_parser("compile", help="QML or IR to generated LVGL C")
    p_compile.add_argument("input", type=Path, help="Input .qml, .qvglir, or .qvglir.json")
    p_compile.add_argument("-o", "--output", type=Path, required=True, help="Output directory")
    p_compile.add_argument("--lvgl-path", type=Path, default=Path("../lvgl"))
    p_compile.add_argument("--profile", type=Path, default=None)
    p_compile.add_argument("--ir-out", type=Path, default=None, help="Write intermediate .qvglir")

    p_preview = sub.add_parser("preview", help="Run SDL/LVGL preview on generated UI directory")
    p_preview.add_argument("gen_dir", type=Path, help="Generated UI directory (ui_*.c/h)")
    p_preview.add_argument("--preview-bin", type=Path, default=None, help="qvgl_preview executable")
    p_preview.add_argument("--headless", action="store_true")
    p_preview.add_argument("--pressure", type=float, default=None, help="legacy alias for --set pressure=")
    p_preview.add_argument("--set", action="append", default=[], metavar="NAME=FLOAT")
    p_preview.add_argument("--dump-fb", type=Path, default=None)
    p_preview.add_argument("--loop-frames", type=int, default=0)
    p_preview.add_argument("--plot-animate", action="store_true")
    p_preview.add_argument("--exit", dest="exit_after", action="store_true")

    p_check = sub.add_parser("check", help="Parse and sema-check QML against profile")
    p_check.add_argument("input", type=Path)
    p_check.add_argument("--profile", type=Path, default=None)

    p_coverage = sub.add_parser("coverage", help="Report whether QML is supported by profile")
    p_coverage.add_argument("input", type=Path)
    p_coverage.add_argument("--profile", type=Path, default=None)

    p_sdkmerge = sub.add_parser(
        "sdkconfig-merge",
        help="Enable CONFIG_* keys from qvgl_sdkconfig.defaults in sdkconfig",
    )
    p_sdkmerge.add_argument("fragment", type=Path, help="qvgl_sdkconfig.defaults from qvglc compile")
    p_sdkmerge.add_argument("sdkconfig", type=Path, help="Project sdkconfig to update")

    p_conformance = sub.add_parser(
        "conformance",
        help="Run manifest.yaml check tiers (smoke/pass/reference/reject)",
    )
    p_conformance.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to manifest.yaml (default: examples/conformance/manifest.yaml)",
    )

    p_run = sub.add_parser("run", help="Compile QML and open SDL preview (one-shot E2E)")
    p_run.add_argument("input", type=Path, help="Input .qml")
    p_run.add_argument("--build-dir", type=Path, default=Path("build"))
    p_run.add_argument("--lvgl-path", type=Path, default=Path("../lvgl"))
    p_run.add_argument("--headless", action="store_true")
    p_run.add_argument("--pressure", type=float, default=None, help="legacy alias for --set pressure=")
    p_run.add_argument("--set", action="append", default=[], metavar="NAME=FLOAT")
    p_run.add_argument("--profile", type=Path, default=None)
    p_run.add_argument("--loop-frames", type=int, default=0)
    p_run.add_argument("--plot-animate", action="store_true")
    p_run.add_argument("--exit", dest="exit_after", action="store_true")

    args = parser.parse_args(argv)

    try:
        if args.cmd == "ir":
            mod = load_json_path(args.input)
            validate(mod)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(encode_module(mod))
            return 0

        if args.cmd == "dump":
            data = args.input.read_bytes()
            mod = decode_binary(data)
            validate(mod)
            print(json.dumps(module_to_dict(mod), indent=2, sort_keys=False))
            return 0

        if args.cmd == "validate":
            mod = load_json_path(args.input)
            validate(mod)
            print(f"ok: {args.input}")
            return 0

        if args.cmd == "emit":
            mod = _load_module(args.input)
            validate(mod)
            caps = probe_lvgl(args.lvgl_path)
            paths = emit_module(mod, caps, args.output)
            for p in paths:
                print(p)
            return 0

        if args.cmd == "compile":
            if args.input.suffix == ".qml":
                prof = load_profile(args.profile or default_profile_path())
                mod = compile_qml(args.input, prof)
            else:
                mod = _load_module(args.input)
            validate(mod)
            if args.ir_out:
                args.ir_out.parent.mkdir(parents=True, exist_ok=True)
                args.ir_out.write_bytes(encode_module(mod))
            caps = probe_lvgl(args.lvgl_path)
            asset_root = args.input.parent if args.input.suffix == ".qml" else None
            paths = emit_module(mod, caps, args.output, asset_root=asset_root)
            for p in paths:
                print(p)
            return 0

        if args.cmd == "preview":
            gen_dir = args.gen_dir.resolve()
            if not gen_dir.is_dir():
                raise EmitError(f"not a directory: {gen_dir}")

            preview_bin = args.preview_bin
            if preview_bin is None:
                env_bin = os.environ.get("QVGL_PREVIEW_BIN")
                if env_bin:
                    preview_bin = Path(env_bin)
                else:
                    preview_bin = Path("build/tests/preview/qvgl_preview")

            cmd = [str(preview_bin), "--gen-dir", str(gen_dir)]
            if args.headless:
                cmd.append("--headless")
            for item in args.set:
                cmd.extend(["--set", item])
            if args.pressure is not None:
                cmd.extend(["--pressure", str(args.pressure)])
            if args.dump_fb:
                cmd.extend(["--dump-fb", str(args.dump_fb)])
            if args.loop_frames:
                cmd.extend(["--loop-frames", str(args.loop_frames)])
            if args.plot_animate:
                cmd.append("--plot-animate")
            if args.exit_after:
                cmd.append("--exit")

            env = os.environ.copy()
            if args.headless and "SDL_VIDEODRIVER" not in env:
                env["SDL_VIDEODRIVER"] = "dummy"

            return subprocess.call(cmd, env=env)

        if args.cmd == "check":
            prof = load_profile(args.profile or default_profile_path())
            check_qml(args.input, prof)
            print(f"ok: {args.input}")
            return 0

        if args.cmd == "coverage":
            prof = load_profile(args.profile or default_profile_path())
            ok, msg = coverage_report(args.input, prof)
            print(msg)
            return 0 if ok else 1

        if args.cmd == "sdkconfig-merge":
            if not args.fragment.is_file():
                raise EmitError(f"fragment not found: {args.fragment}")
            if not args.sdkconfig.is_file():
                raise EmitError(f"sdkconfig not found: {args.sdkconfig}")
            changed = merge_sdkconfig_fragment(args.fragment, args.sdkconfig)
            print(f"{'updated' if changed else 'ok'}: {args.sdkconfig}")
            return 0

        if args.cmd == "conformance":
            code, errors = run_conformance_checks(args.manifest)
            if errors:
                for line in errors:
                    print(line, file=sys.stderr)
                return code
            print("ok: conformance manifest")
            return 0

        if args.cmd == "run":
            if args.input.suffix != ".qml":
                raise EmitError("run requires a .qml file")
            return run_qml_preview(
                args.input,
                build_dir=args.build_dir,
                lvgl_path=args.lvgl_path,
                profile_path=args.profile,
                headless=args.headless,
                pressure=args.pressure,
                prop_sets=args.set,
                loop_frames=args.loop_frames,
                plot_animate=args.plot_animate,
                exit_after=args.exit_after,
            )

    except (QvglDiagnostic, EmitError, Exception) as e:
        print(f"qvglc: {e}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
