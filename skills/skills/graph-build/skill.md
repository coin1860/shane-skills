---
name: graph-build
description: Build a knowledge graph from any folder of files → clustered communities → HTML + JSON + GRAPH_REPORT.md
trigger: /graph-build
---

# /graphify

Turn any folder of files into a navigable knowledge graph with community detection, an honest audit trail, and three outputs: interactive HTML, GraphRAG-ready JSON, and a plain-language GRAPH_REPORT.md.

## Usage

```
/graph-build                     # full pipeline on current directory
/graph-build <path>              # full pipeline on specific path
/graph-build <path> --update     # incremental - re-extract only new/changed files
/graph-build <path> --no-viz     # skip visualization, just report + JSON
/graph-build <path> --wiki       # build agent-crawlable wiki
```

## What You Must Do When Invoked

If no path was given, use `.` (current directory). Do not ask the user for a path.

Follow these steps in order. Do not skip steps.

**All commands use `python -c "..."` syntax — no bash heredocs, no shell redirects, no `&&`/`||`. This runs correctly on Windows PowerShell and macOS/Linux alike.**

### Step 1 - Ensure graphify is installed

```python
python -c "import graphify; import sys; from pathlib import Path; Path('graphify-out').mkdir(exist_ok=True); Path('graphify-out/.graphify_python').write_text(sys.executable)"
```

If the import fails, install first:

```python
python -m pip install graphifyy -q
```

Then re-run the Step 1 command.

### Step 2 - Detect files

```python
python -c "
import json, sys
from graphify.detect import detect
from pathlib import Path

result = detect(Path('INPUT_PATH'))
Path('graphify-out/.graphify_detect.json').write_text(json.dumps(result, indent=2))
total = result.get('total_files', 0)
words = result.get('total_words', 0)
print(f'Corpus: {total} files, ~{words} words')
for ftype, files in result.get('files', {}).items():
    if files:
        print(f'  {ftype}: {len(files)} files')
"
```

Replace `INPUT_PATH` with the actual path. Present a clean summary — do not dump the raw JSON.

- If `total_files` is 0: stop with "No supported files found in [path]."
- If `total_words` > 2,000,000 OR `total_files` > 200: warn the user and ask which subfolder to run on.
- Otherwise: proceed to Step 3.

### Step 3 - Extract entities and relationships

#### Part A - Structural extraction (AST, free, no API cost)

```python
python -c "
import json
from graphify.extract import collect_files, extract
from pathlib import Path

detect = json.loads(Path('graphify-out/.graphify_detect.json').read_text())
code_files = []
for f in detect.get('files', {}).get('code', []):
    p = Path(f)
    code_files.extend(collect_files(p) if p.is_dir() else [p])

if code_files:
    result = extract(code_files)
    Path('graphify-out/.graphify_ast.json').write_text(json.dumps(result, indent=2))
    print(f'AST: {len(result[\"nodes\"])} nodes, {len(result[\"edges\"])} edges')
else:
    Path('graphify-out/.graphify_ast.json').write_text(json.dumps({'nodes':[],'edges':[],'input_tokens':0,'output_tokens':0}))
    print('No code files - skipping AST extraction')
"
```

#### Part B - Semantic extraction (parallel subagents)

Skip if corpus is code-only (no docs, papers, or images).

**Step B0 — Check cache**

```python
python -c "
import json
from graphify.cache import check_semantic_cache
from pathlib import Path

detect = json.loads(Path('graphify-out/.graphify_detect.json').read_text())
all_files = [f for files in detect['files'].values() for f in files]
cached_nodes, cached_edges, cached_hyperedges, uncached = check_semantic_cache(all_files)

if cached_nodes or cached_edges:
    Path('graphify-out/.graphify_cached.json').write_text(json.dumps({'nodes': cached_nodes, 'edges': cached_edges, 'hyperedges': cached_hyperedges}))
Path('graphify-out/.graphify_uncached.txt').write_text('\n'.join(uncached))
print(f'Cache: {len(all_files)-len(uncached)} hit, {len(uncached)} need extraction')
"
```


If `graphify-out/.graphify_uncached.txt` is empty (all files cached), skip to Part C.

**Step B1 — Split uncached files into chunks**

Load the uncached file list. Split into chunks of **15 files** each. Group files from the same directory together. Images get their own chunk of max 5 (vision is token-heavy).

Print: `Semantic extraction: ~N files → X subagents, estimated ~Ys`

**Step B2 — Dispatch ALL subagents in one message (parallel)**

> **MANDATORY**: Call `runSubagent("graphify-extractor", ...)` once per chunk, **all in the same response**. Sequential calls are 5-10× slower.

For each chunk, substitute FILE_LIST, CHUNK_NUM, TOTAL_CHUNKS:

```
Extract chunk CHUNK_NUM of TOTAL_CHUNKS.

Files to process:
FILE_LIST

Write your output to: graphify-out/.graphify_chunk_CHUNK_NUM.json
```

**Step B3 — Collect results and save cache**

Wait for all subagents. For each `graphify-out/.graphify_chunk_N.json`:
- File exists + valid `nodes`/`edges` → include
- File missing → print `chunk N missing — skipping`
- More than half chunks missing → stop, tell user to re-run

```python
python -c "
import json, glob
from graphify.cache import save_semantic_cache
from pathlib import Path

new_nodes, new_edges, new_hyperedges = [], [], []
for f in sorted(glob.glob('graphify-out/.graphify_chunk_*.json')):
    try:
        c = json.loads(Path(f).read_text())
        new_nodes.extend(c.get('nodes', []))
        new_edges.extend(c.get('edges', []))
        new_hyperedges.extend(c.get('hyperedges', []))
    except Exception as e:
        print(f'Warning: {f} unreadable: {e}')

Path('graphify-out/.graphify_semantic_new.json').write_text(
    json.dumps({'nodes': new_nodes, 'edges': new_edges, 'hyperedges': new_hyperedges,
                'input_tokens': 0, 'output_tokens': 0}))
if new_nodes or new_edges:
    save_semantic_cache(new_nodes, new_edges, new_hyperedges)
    print(f'{len(new_nodes)} nodes, {len(new_edges)} edges cached')
"
```

#### Part C - Merge cached + new + AST

```python
python -c "
import json
from pathlib import Path

ast    = json.loads(Path('graphify-out/.graphify_ast.json').read_text())
cached = json.loads(Path('graphify-out/.graphify_cached.json').read_text()) if Path('graphify-out/.graphify_cached.json').exists() else {'nodes':[],'edges':[],'hyperedges':[]}
new    = json.loads(Path('graphify-out/.graphify_semantic_new.json').read_text()) if Path('graphify-out/.graphify_semantic_new.json').exists() else {'nodes':[],'edges':[],'hyperedges':[]}

all_nodes = list(ast.get('nodes', []))
all_edges = list(ast.get('edges', []))
all_hyperedges = []
seen = {n['id'] for n in all_nodes}

for n in (cached.get('nodes', []) + new.get('nodes', [])):
    if n['id'] not in seen:
        all_nodes.append(n)
        seen.add(n['id'])
all_edges      += cached.get('edges', [])      + new.get('edges', [])
all_hyperedges += cached.get('hyperedges', []) + new.get('hyperedges', [])

merged = {'nodes': all_nodes, 'edges': all_edges, 'hyperedges': all_hyperedges,
          'input_tokens': 0, 'output_tokens': 0}
Path('graphify-out/.graphify_extract.json').write_text(json.dumps(merged, indent=2))
print(f'Merged: {len(all_nodes)} nodes, {len(all_edges)} edges ({len(ast[\"nodes\"])} AST + {len(all_nodes)-len(ast[\"nodes\"])} semantic)')
"
```

Clean up:

```python
python -c "
import glob, os
for f in (glob.glob('graphify-out/.graphify_chunk_*.json') +
          ['graphify-out/.graphify_cached.json',
           'graphify-out/.graphify_semantic_new.json',
           'graphify-out/.graphify_uncached.txt']):
    try: os.remove(f)
    except FileNotFoundError: pass
"
```

### Step 4 - Build graph and cluster

```python
python -c "
import json
from graphify.build import build_from_json
from graphify.cluster import cluster
from graphify.analyze import god_nodes, surprising_connections
from pathlib import Path

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text())
G = build_from_json(extraction)
communities = cluster(G)
gods = god_nodes(G)
surprises = surprising_connections(G, communities)

import networkx as nx
from networkx.readwrite import json_graph
graph_data = json_graph.node_link_data(G)
Path('graphify-out/graph.json').write_text(json.dumps(graph_data, indent=2))
Path('graphify-out/.graphify_analysis.json').write_text(json.dumps({
    'communities': {str(k): v for k, v in communities.items()},
    'cohesion': {},
    'god_nodes': gods,
    'surprises': surprises,
}, indent=2))
print(f'Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {len(communities)} communities')
print(f'God nodes: {[g[\"label\"] for g in gods[:5]]}')
"
```

### Step 5 - Label communities

Read `graphify-out/.graphify_analysis.json`. For each community key, look at its node labels and write a 2-5 word plain-language name (e.g. "Attention Mechanism", "Training Pipeline", "Data Loading").

Then regenerate the report and save the labels for the visualizer:

```python
python -c "
import json
from graphify.build import build_from_json
from graphify.cluster import score_all
from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.report import generate
from pathlib import Path

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text())
analysis   = json.loads(Path('graphify-out/.graphify_analysis.json').read_text())

G = build_from_json(extraction)
communities = {int(k): v for k, v in analysis['communities'].items()}
cohesion = {int(k): v for k, v in analysis.get('cohesion', {}).items()}
tokens = {'input': extraction.get('input_tokens', 0), 'output': extraction.get('output_tokens', 0)}

# LABELS - replace these with the names you chose above
labels = LABELS_DICT

questions = suggest_questions(G, communities, labels)

report = generate(G, communities, cohesion, labels, analysis['god_nodes'], analysis['surprises'], {}, tokens, 'INPUT_PATH', suggested_questions=questions)
Path('graphify-out/GRAPH_REPORT.md').write_text(report)
Path('graphify-out/.graphify_labels.json').write_text(json.dumps({str(k): v for k, v in labels.items()}))
print('Report updated with community labels')
"
```

Replace `LABELS_DICT` with the actual dict you constructed (e.g. `{0: "Attention Mechanism", 1: "Training Pipeline"}`).
Replace `INPUT_PATH` with the actual path.

### Step 6 - Generate report and visualization

```python
python -c "
import json
from graphify.build import build_from_json
from graphify.cluster import score_all
from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.report import generate
from pathlib import Path

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text())
analysis   = json.loads(Path('graphify-out/.graphify_analysis.json').read_text())
labels_raw = json.loads(Path('graphify-out/.graphify_labels.json').read_text()) if Path('graphify-out/.graphify_labels.json').exists() else {}
detect     = json.loads(Path('graphify-out/.graphify_detect.json').read_text())

G           = build_from_json(extraction)
communities = {int(k): v for k, v in analysis['communities'].items()}
labels      = {int(k): v for k, v in labels_raw.items()}
cohesion    = score_all(G, communities)
gods        = god_nodes(G)
surprises   = surprising_connections(G, communities)
questions   = suggest_questions(G, communities, labels)
token_cost  = {'input': extraction.get('input_tokens', 0), 'output': extraction.get('output_tokens', 0)}

report = generate(G, communities, cohesion, labels, gods, surprises, detect, token_cost, 'INPUT_PATH', suggested_questions=questions)
Path('graphify-out/GRAPH_REPORT.md').write_text(report)
print('GRAPH_REPORT.md written')
"
```

Replace `INPUT_PATH` with the actual corpus path used in Step 2.

```python
python -c "
import json
from graphify.build import build_from_json
from graphify.export import to_html
from pathlib import Path

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text())
analysis   = json.loads(Path('graphify-out/.graphify_analysis.json').read_text())
labels_raw = json.loads(Path('graphify-out/.graphify_labels.json').read_text()) if Path('graphify-out/.graphify_labels.json').exists() else {}

G           = build_from_json(extraction)
communities = {int(k): v for k, v in analysis['communities'].items()}  # reuse Step 4 result, don't re-cluster
labels      = {int(k): v for k, v in labels_raw.items()}

try:
    to_html(G, communities, 'graphify-out/graph.html', community_labels=labels or None)
    print('graph.html written')
except ValueError as e:
    print(f'Visualization skipped: {e}')
"
```

### Step 6b - Wiki (only if --wiki flag)

**Only run this step if `--wiki` was explicitly given in the original command.**

```python
python -c "
import json
from graphify.build import build_from_json
from graphify.wiki import to_wiki
from graphify.analyze import god_nodes
from pathlib import Path

extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text())
analysis   = json.loads(Path('graphify-out/.graphify_analysis.json').read_text())
labels_raw = json.loads(Path('graphify-out/.graphify_labels.json').read_text()) if Path('graphify-out/.graphify_labels.json').exists() else {}

G = build_from_json(extraction)
communities = {int(k): v for k, v in analysis['communities'].items()}
cohesion = {int(k): v for k, v in analysis.get('cohesion', {}).items()}
labels = {int(k): v for k, v in labels_raw.items()}
gods = god_nodes(G)

n = to_wiki(G, communities, 'graphify-out/wiki', community_labels=labels or None, cohesion=cohesion, god_nodes_data=gods)
print(f'Wiki: {n} articles written to graphify-out/wiki/')
print('  graphify-out/wiki/index.md  ->  agent entry point')
"
```

### After completing all steps

Print this summary:

```
graphify complete
  graph.json      — GraphRAG-ready, queryable by /graphify query
  graph.html      — interactive visualization (open in browser)
  GRAPH_REPORT.md — plain-language architecture summary
  wiki/           — agent-crawlable wiki (only if --wiki was given)
```

Read `graphify-out/GRAPH_REPORT.md` and share the **God Nodes** and **Surprising Connections** sections directly in the chat — do not ask the user to open the file themselves.

Then immediately offer to explore. Pick the single most interesting suggested question from the report and ask:

> "The most interesting question this graph can answer: **[question]**. Want me to trace it?"

If the user says yes, use `/graph-query` to walk them through the answer.
