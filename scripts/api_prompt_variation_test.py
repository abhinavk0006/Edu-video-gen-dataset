from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request


def default_variants() -> list[str]:
    return [
        "A chemistry titration experiment in a school laboratory. A glass burette drips clear solution into a conical flask. The solution changes from colourless to pale pink at the endpoint. Bright classroom lighting, realistic educational lab setup.",
        "A close-up detailed chemistry titration scene. The burette drips slowly, the flask is swirled, and a faint pink endpoint appears. Realistic lab glassware, professional camera framing, educational science video.",
        "A slow-motion chemistry titration in a school lab. The burette releases drops, the student swirls the flask, and the liquid turns pale pink at the endpoint at the final drop. Clean lab background, realistic lighting.",
        "A physics laboratory setup showing a resistor circuit with current and voltage measurement. Wires, multimeter, resistor board, clean lab bench, educational demonstration style.",
        "A classroom science experiment demonstrating diffusion of ink in water. Blue ink slowly spreads into clear water. Calm, educational, realistic, macro shot, natural motion.",
    ]


def load_prompt_bundle(path: str) -> list[str]:
    bundle = json.loads(Path(path).read_text(encoding="utf-8"))
    prompts = [item.get("prompt") for item in bundle.get("prompt_inputs", [])]
    variants = [prompt for prompt in prompts if isinstance(prompt, str) and prompt.strip()]
    if not variants:
        raise ValueError(f"No prompts found in bundle: {path}")
    return variants


def extract_output(response_json: dict[str, Any]) -> str:
    candidates = [
        response_json.get("video_url"),
        response_json.get("output_url"),
        response_json.get("url"),
        response_json.get("file_url"),
        response_json.get("result"),
        response_json.get("output"),
    ]
    for item in candidates:
        if isinstance(item, str) and item.strip():
            return item

    for container_name in ["data", "result"]:
        container = response_json.get(container_name)
        if isinstance(container, dict):
            for key in ["video_url", "output_url", "url", "file_url"]:
                value = container.get(key)
                if isinstance(value, str) and value.strip():
                    return value

    return json.dumps(response_json, ensure_ascii=False)


def call_api(
    url: str,
    prompt: str,
    *,
    variant_index: int,
    negative_prompt: str,
    seed: int,
    fps: int = 8,
) -> dict[str, Any]:
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "seed": seed,
        "variant_index": variant_index,
        "fps": fps,
        "num_frames": 16,
        "width": 768,
        "height": 432,
        "output_format": "mp4",
    }
    request = urllib_request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(request, timeout=180) as response:
            response_text = response.read().decode("utf-8")
    except urllib_error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    except urllib_error.URLError as exc:
        raise RuntimeError(f"Could not connect to API: {exc.reason}") from exc

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return {"raw_response": response_text}


def run_variations(
    url: str,
    variants: list[str],
    negative_prompt: str,
    *,
    base_seed: int = 42,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for index, prompt in enumerate(variants):
        seed = base_seed + index
        print(f"\n=== Variant {index + 1}/{len(variants)} ===")
        print(f"Seed: {seed}")
        print(f"Prompt: {prompt}\n")
        try:
            response_json = call_api(
                url,
                prompt,
                variant_index=index,
                negative_prompt=negative_prompt,
                seed=seed,
            )
            output = extract_output(response_json)
            results.append({
                "variant_index": index,
                "seed": seed,
                "prompt": prompt,
                "response": response_json,
                "output": output,
            })
            print(f"Output: {output}")
        except Exception as exc:  # pragma: no cover - user-facing diagnostic path
            print(f"ERROR: variant {index + 1} failed: {exc}")
            results.append({
                "variant_index": index,
                "seed": seed,
                "prompt": prompt,
                "error": str(exc),
            })
        time.sleep(0.5)
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run prompt variations against a video generation API."
    )
    parser.add_argument(
        "--url",
        default=os.getenv("VIDEO_API_URL", "http://localhost:8000/generate"),
        help="API endpoint to call.",
    )
    parser.add_argument(
        "--negative-prompt",
        default=os.getenv(
            "NEGATIVE_PROMPT",
            "blurry, low quality, distorted, bad anatomy, text artifacts, watermark",
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=int(os.getenv("VIDEO_SEED", "42")),
    )
    parser.add_argument(
        "--variants",
        nargs="*",
        default=None,
        help="Optional list of custom prompt variants. If omitted, defaults are used.",
    )
    parser.add_argument(
        "--prompts-file",
        default=None,
        help="JSON prompt bundle created by build_rag_prompt_bundle.py.",
    )
    parser.add_argument("--json-output", default=None, help="Path to save results as JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.prompts_file:
        variants = load_prompt_bundle(args.prompts_file)
    else:
        variants = args.variants if args.variants else default_variants()

    print(f"Calling video API: {args.url}")
    print(f"Variants to test: {len(variants)}")
    results = run_variations(args.url, variants, args.negative_prompt, base_seed=args.seed)

    if args.json_output:
        output_path = os.path.abspath(args.json_output)
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(results, handle, ensure_ascii=False, indent=2)
        print(f"\nSaved results JSON to: {output_path}")

    print("\nSummary")
    for item in results:
        if "error" in item:
            print(f"Variant {item['variant_index'] + 1}: ERROR -> {item['error']}")
        else:
            print(f"Variant {item['variant_index'] + 1}: ok -> {item['output'][:200]}")


if __name__ == "__main__":
    main()
