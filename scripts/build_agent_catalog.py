#!/usr/bin/env python3
"""Build the SendSprint agent catalog as a HAMT (spec YOOL_TUPLE_HAMT v0.2).

Scans `sendsprint.agent_registry.default_agent_registry()` (canonical source
of truth for yools) and writes `.catalog/agents.json` with the spec-shaped
payload:

    {
      "meta": {...},
      "flat": { yool_id: {hash, hash_hex, slots, tuple} },
      "trie": <nested node/leaf/collision>
    }

Hash:
    blake2b-64 truncated to 30 bits, 5 bits/level, 6 levels, branching=32.

CI gate:
    `python scripts/build_agent_catalog.py --check` exits 1 if drift.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sendsprint.agent_registry import (  # noqa: E402
    AgentCapability,
    AgentProvider,
    AgentRegistry,
    default_agent_registry,
)

BITS_PER_LEVEL = 5
BRANCH = 1 << BITS_PER_LEVEL
MAX_LEVELS = 6
HASH_BITS = BITS_PER_LEVEL * MAX_LEVELS
DEFAULT_OUTPUT = PROJECT_ROOT / ".catalog" / "agents.json"
DEFAULT_CPU_PCT = 60
DEFAULT_DISK_MB = 100
DEFAULT_TIMEOUT_S = 300


def yool_hash(yool_id: str) -> int:
    digest = hashlib.blake2b(yool_id.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") & ((1 << HASH_BITS) - 1)


def slot_at(h: int, level: int) -> int:
    shift = (MAX_LEVELS - 1 - level) * BITS_PER_LEVEL
    return (h >> shift) & (BRANCH - 1)


def yool_slots(h: int) -> list[int]:
    return [slot_at(h, lvl) for lvl in range(MAX_LEVELS)]


@dataclass
class Leaf:
    key: str
    hash: int
    tuple: dict[str, Any]
    kind: str = "leaf"


@dataclass
class Collision:
    hash_prefix: int
    leaves: list[Leaf] = field(default_factory=list)
    kind: str = "collision"


@dataclass
class Node:
    bitmap: int = 0
    children: dict[int, Any] = field(default_factory=dict)
    kind: str = "node"


def insert(root: Node, leaf: Leaf, level: int = 0) -> None:
    if level >= MAX_LEVELS:
        slot = leaf.hash & (BRANCH - 1)
        existing = root.children.get(slot)
        if existing is None:
            root.bitmap |= 1 << slot
            root.children[slot] = Collision(hash_prefix=leaf.hash, leaves=[leaf])
        elif isinstance(existing, Collision):
            existing.leaves.append(leaf)
        else:
            raise RuntimeError("unexpected node at collision depth")
        return

    slot = slot_at(leaf.hash, level)
    existing = root.children.get(slot)

    if existing is None:
        root.bitmap |= 1 << slot
        root.children[slot] = leaf
        return

    if isinstance(existing, Leaf):
        if existing.hash == leaf.hash and existing.key == leaf.key:
            existing.tuple = leaf.tuple
            return
        sub = Node()
        insert(sub, existing, level + 1)
        insert(sub, leaf, level + 1)
        root.children[slot] = sub
        return

    if isinstance(existing, Node):
        insert(existing, leaf, level + 1)
        return

    raise RuntimeError(f"unexpected child kind: {type(existing)}")


def trie_to_json(node: Any) -> Any:
    if isinstance(node, Leaf):
        return {
            "kind": "leaf",
            "key": node.key,
            "hash": f"{node.hash:030b}",
            "tuple": node.tuple,
        }
    if isinstance(node, Collision):
        return {
            "kind": "collision",
            "hash_prefix": f"{node.hash_prefix:030b}",
            "leaves": [trie_to_json(leaf) for leaf in node.leaves],
        }
    if isinstance(node, Node):
        return {
            "kind": "node",
            "bitmap": f"{node.bitmap:032b}",
            "popcount": bin(node.bitmap).count("1"),
            "children": {
                str(slot): trie_to_json(child)
                for slot, child in sorted(node.children.items())
            },
        }
    raise TypeError(node)


def tuple_for_capability(provider: AgentProvider, cap: AgentCapability) -> dict[str, Any]:
    return {
        "yool_id": f"agent.{provider.key}.{cap.key}",
        "authority": provider.key,
        "lane": cap.key,
        "runtime": provider.runtime,
        "name": provider.name,
        "description": cap.description,
        "cost_profile": cap.cost_profile,
        "parallel_safe": cap.parallel_safe,
        "requires_clean_worktree": cap.requires_clean_worktree,
        "inputs": ["payload"],
        "outputs": ["receipt"],
        "guardrails": {
            "cpu_quota_pct": DEFAULT_CPU_PCT,
            "disk_quota_mb": DEFAULT_DISK_MB,
            "timeout_s": DEFAULT_TIMEOUT_S,
        },
    }


def build_catalog(registry: AgentRegistry | None = None) -> dict[str, Any]:
    registry = registry if registry is not None else default_agent_registry()
    root = Node()
    flat: dict[str, dict[str, Any]] = {}
    count = 0
    for provider in registry.providers:
        for cap in provider.capabilities:
            yool_id = f"agent.{provider.key}.{cap.key}"
            tup = tuple_for_capability(provider, cap)
            h = yool_hash(yool_id)
            leaf = Leaf(key=yool_id, hash=h, tuple=tup)
            insert(root, leaf)
            flat[yool_id] = {
                "hash": f"{h:030b}",
                "hash_hex": f"{h:08x}",
                "slots": yool_slots(h),
                "tuple": tup,
            }
            count += 1
    return {
        "meta": {
            "source": "sendsprint.agent_registry.default_agent_registry",
            "count": count,
            "branching": BRANCH,
            "bits_per_level": BITS_PER_LEVEL,
            "max_levels": MAX_LEVELS,
            "hash_bits": HASH_BITS,
            "hash_algo": "blake2b-64bit-truncated-to-30bit",
            "spec": "YOOL_TUPLE_HAMT v0.2",
        },
        "flat": dict(sorted(flat.items())),
        "trie": trie_to_json(root),
    }


def canonical_json(catalog: dict[str, Any]) -> str:
    return json.dumps(catalog, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build SendSprint agent HAMT catalog")
    parser.add_argument(
        "-o", "--output", default=str(DEFAULT_OUTPUT), help="output JSON path"
    )
    parser.add_argument(
        "--stdout", action="store_true", help="print catalog JSON to stdout"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if --output differs from freshly built catalog",
    )
    args = parser.parse_args(argv)

    catalog = build_catalog()
    text = canonical_json(catalog)

    if args.stdout:
        sys.stdout.write(text)
        return 0

    target = Path(args.output)
    if args.check:
        if not target.exists():
            print(f"missing: {target}", file=sys.stderr)
            return 1
        existing = target.read_text(encoding="utf-8")
        if existing != text:
            print(f"DRIFT: regenerate {target}", file=sys.stderr)
            return 1
        print(f"OK: {target} matches registry ({catalog['meta']['count']} yools)")
        return 0

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(
        f"wrote {catalog['meta']['count']} yools -> {target} "
        f"(branching={BRANCH}, levels={MAX_LEVELS})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
