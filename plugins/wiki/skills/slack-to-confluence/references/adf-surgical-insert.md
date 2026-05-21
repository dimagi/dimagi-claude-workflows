# ADF Surgical Insert — Reference

This document describes the pattern for editing a Confluence page without disturbing any other content. Use this any time the page has images, tables, panels, macros, layouts, or any rich formatting.

## Why not markdown?

The Atlassian Confluence MCP supports two body formats: `markdown` and `adf` (Atlassian Document Format, JSON).

**Markdown round-trip is destructive.** When you GET a page as markdown, Confluence converts internal storage format → markdown. When you POST it back, it converts markdown → storage format. Even an identity round-trip (read, then write the same content) typically changes:

- Image placement and sizing
- Table column widths and styling
- Panel macros (info/warning/success panels become plain blockquotes or get stripped)
- Smart-quote and non-breaking-space normalization
- List numbering and nesting
- Layouts (multi-column layouts collapse)

ADF is the page's native tree representation. A round-trip is byte-identical, so you can splice in one node and leave everything else alone.

## The pattern

### 1. Fetch the page as ADF

```
getConfluencePage(cloudId="dimagi.atlassian.net", pageId=<ID>, contentFormat="adf")
```

The response will almost always be too large to return inline (typical pages are 100KB+ of JSON). The MCP saves it to a file at a path it includes in the error message, formatted as:

```
[{"type": "text", "text": "<full JSON response as string>"}]
```

### 2. Locate the saved file in the workspace

The file is saved on the host's `.claude/projects/` path. In the bash sandbox it appears under `/sessions/<session>/mnt/.claude/projects/.../tool-results/mcp-...-getConfluencePage-<ts>.txt`. Use `find` to locate it:

```bash
find /sessions/*/mnt/.claude -name "*getConfluencePage*" -newer /tmp/marker 2>/dev/null
```

(Touch `/tmp/marker` before the fetch so you only see the file from this call.)

### 3. Extract the ADF body

```python
import json
with open(saved_path) as f:
    wrapper = json.load(f)          # list[{"type": "text", "text": "..."}]
page = json.loads(wrapper[0]["text"])  # the page dict
adf = page["body"]                  # the ADF doc (dict)
# adf has keys: type ("doc"), content (list of block nodes), version
```

Save to `outputs/page_adf.json` for inspection and downstream use.

### 4. Find the target heading by walking content[]

```python
def node_text(n):
    if n.get("type") == "text":
        return n.get("text", "")
    return "".join(node_text(c) for c in (n.get("content") or []))

target_idx = None
for i, node in enumerate(adf["content"]):
    if node.get("type") == "heading" and "Configure data forwarding" in node_text(node):
        target_idx = i
        break
```

Print 2-3 nodes of context on each side for the user-facing diff preview.

### 5. Build the new node

Common ADF node patterns:

**Info panel:**

```json
{
  "type": "panel",
  "attrs": {"panelType": "info"},
  "content": [
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "Note: ", "marks": [{"type": "strong"}]},
        {"type": "text", "text": "Body of the note."}
      ]
    }
  ]
}
```

`panelType` options: `"info"` (blue), `"note"` (purple), `"warning"` (yellow), `"success"` (green), `"error"` (red).

**Paragraph with mixed formatting:**

```json
{
  "type": "paragraph",
  "content": [
    {"type": "text", "text": "Plain text "},
    {"type": "text", "text": "bold bit", "marks": [{"type": "strong"}]},
    {"type": "text", "text": " then plain again."}
  ]
}
```

**Heading:**

```json
{
  "type": "heading",
  "attrs": {"level": 4},
  "content": [{"type": "text", "text": "Heading text"}]
}
```

### 6. Splice and minify

```python
adf["content"].insert(target_idx + 1, new_node)  # insert AFTER the target heading
with open("outputs/page_adf_modified.json", "w") as f:
    json.dump(adf, f, separators=(",", ":"))     # minify
```

For easier chunk-reading via the Read tool, also produce a version with each top-level node on its own line:

```python
out = ['{"type":"doc","content":[']
for i, node in enumerate(adf["content"]):
    line = json.dumps(node, separators=(",", ":"))
    if i < len(adf["content"]) - 1: line += ","
    out.append(line)
out.append('],"version":' + json.dumps(adf.get("version", 1)) + "}")
with open("outputs/page_adf_lined.json", "w") as f:
    f.write("\n".join(out))
```

This lets you read the file back in chunks via Read with `offset`/`limit` (each line stays under the per-read token limit).

### 7. Write back

The `body` parameter to `updateConfluencePage` is a string. You'll need to read the file (in chunks if necessary) and pass the full JSON as the body:

```
updateConfluencePage(
  cloudId="dimagi.atlassian.net",
  pageId=<ID>,
  contentFormat="adf",
  title=<unchanged title>,
  versionMessage="<traceable message>",
  body=<full ADF JSON as a single-line string>
)
```

**Cost note:** the body parameter often runs 30K-80K characters (10K-25K output tokens). That's an unavoidable cost of an ADF write through the MCP — it's still much cheaper than the cost of corrupting a wiki page.

## Insertion-point conventions

For a clarifying note under an existing heading:

- Insert **after** the first paragraph that follows the heading (not immediately after the heading)
- This lets the heading's own introductory sentence breathe before the note interrupts

For a section rewrite:

- Identify the start (the heading node) and end (next heading at same or higher level)
- Replace the range `content[start+1 : end]` with new nodes

For a new section:

- Insert a heading node + supporting content nodes at the boundary of the previous section

## Sanity checks

Before writing, programmatically verify:

- `len(content)` increased by exactly the number of nodes inserted
- The target heading is still at the index you expect (i.e., the surrounding nodes weren't disturbed)
- The new node is valid ADF (at minimum: has a `type`, and if it has a `content` array, each child has a `type`)

After writing, verify the API returned an incremented version number with your version message attached.

## Common mistakes

- **Forgetting `contentFormat="adf"` on the write.** If you omit it, Confluence will try to interpret your JSON as markdown.
- **Indented JSON.** Confluence accepts it but it's wasteful in the body parameter. Minify.
- **Including `localId` on a brand-new node when it conflicts with existing IDs.** Safest: omit `localId` on inserted nodes and let Confluence assign one.
- **Editing inside a `mediaSingle` or `table` node.** Those are nested structures — don't pass them as top-level content. Walk into `content[i].content[j]` when needed.
