# Architecture — wp-ml-translate

Technical documentation for how the system works internally.

---

## System Design

```mermaid
graph TD
    CLI["wp-ml-translate.py<br/>(CLI router)"]

    CLI --> init
    CLI --> fetch
    CLI --> translate
    CLI --> apply
    CLI --> submit

    init --> terminal["Interactive terminal"]
    fetch --> fetcher["lib/fetcher.py"]
    translate --> translator["lib/translator.py"]
    apply --> translator
    submit --> submitter["lib/submitter.py"]

    fetcher --> glotpress["GlotPress<br/>(scrape)"]
    translator --> context["context/<br/>prompt-template.md"]
    translator --> datadir["data/&lt;slug&gt;/<br/>strings.json"]
    submitter --> browser["Browser<br/>localhost:8787"]
```

## Data Flow (Overview)

```mermaid
flowchart LR
    A["URL / Slug"] --> B["Fetch"]
    B --> C["Translate"]
    C --> D["AI"]
    D --> E["Apply"]
    E -->|"repeat"| C
    E --> F["Submit"]
```

## Data Flow (Detailed)

```mermaid
flowchart TD
    start(["User gives URL or slug"]) --> fetch

    subgraph fetch["FETCH"]
        direction TB
        f1["Parse URL → type + slug"]
        f2["Call GlotPress API for stats"]
        f3["Scrape HTML pages for<br/>pending strings"]
        f4[("data/slug/strings.json")]
        f1 --> f2 --> f3 --> f4
    end

    fetch --> translate

    subgraph translate["TRANSLATE"]
        direction TB
        t1["Load pending strings<br/>from strings.json"]
        t2["Select next batch of N"]
        t_ctx[/"context/prompt-template.md<br/>(rules + glossary)"/]
        t3["Assemble full prompt:<br/>rules + glossary + strings"]
        t4[("data/slug/prompt.md")]
        t1 --> t2 --> t3 --> t4
        t_ctx --> t3
    end

    translate --> userai

    subgraph userai["USER + AI"]
        direction TB
        u1["AI reads prompt.md"]
        u2["AI generates Malayalam<br/>translations as JSON"]
        u3[("data/slug/response.json")]
        u1 --> u2 --> u3
    end

    userai --> apply

    subgraph apply["APPLY"]
        direction TB
        a1["Load response.json"]
        a2["Match translations by ID<br/>→ merge into strings.json"]
        a3["Set status = ready"]
        a4["Archive response file"]
        a1 --> a2 --> a3 --> a4
    end

    apply -->|"repeat if<br/>strings remain"| translate
    apply -->|"all done"| submit

    subgraph submit["SUBMIT"]
        direction TB
        s1["Start local HTTP server"]
        s2["Show next ready string"]
        s3["User: Open GlotPress & Copy"]
        s4["User: Paste → Suggest<br/>on GlotPress"]
        s5["User: Done → Next"]
        s6["Mark submitted in JSON"]
        s1 --> s2 --> s3 --> s4 --> s5 --> s6
        s6 -->|"next string"| s2
    end
```

## Per-Project Data (`data/<slug>/`)

Each project gets its own folder:

```
data/
├── twentyten/
│   ├── strings.json           # Main data file
│   ├── prompt.md              # Latest generated prompt (gitignored)
│   ├── response.json          # AI output before apply (gitignored)
│   └── response_applied.json  # Archived after apply (gitignored)
├── twentytwentyfour/
│   └── ...
└── woocommerce/
    └── ...
```

### strings.json format

```json
{
  "project": {
    "slug": "twentyten",
    "name": "Twenty Ten",
    "type": "wp-themes",
    "url": "https://translate.wordpress.org/projects/wp-themes/twentyten/ml/default/",
    "fetched_at": "2026-08-07T...",
    "stats": {
      "total": 109,
      "translated": 84,
      "pending": 25,
      "percent": 77
    }
  },
  "strings": [
    {
      "id": "315232",
      "status": "untranslated",
      "priority": "high",
      "context": "",
      "original": "The 2010 theme...",
      "plural": "",
      "references": "style.css:0",
      "comment": "Description of the theme",
      "glossary_hits": {"theme": "തീം", "WordPress": "വേഡ്പ്രസ്സ്"},
      "placeholders": [],
      "translation": "...",
      "translation_status": "ready",
      "submitted": false,
      "permalink": "https://..."
    }
  ]
}
```

### String status lifecycle

```mermaid
stateDiagram-v2
    pending --> ready
    ready --> submitted
    ready --> skipped
```

## Components

### Fetcher (`lib/fetcher.py`)

- **URL parsing**: Handles full URLs, locale URLs, type/slug paths, bare slugs
- **API**: `/api/projects/<type>/<slug>` for stats
- **Scraping**: HTML table pagination, 15 rows/page, 0.7s delay between requests
- **Extracts**: original text, plural, context, references, comments, glossary hits, placeholders

### Translator (`lib/translator.py`)

- **`generate_prompt()`**: Assembles prompt-template.md + batch of strings → prompt.md
- **`apply_translations()`**: Parses AI JSON response, merges into strings.json, handles code block wrappers

### Submitter (`lib/submitter.py`)

- Embedded single-page HTML app (no external dependencies)
- HTTP server with `/api/state`, `/api/done`, `/api/skip` endpoints
- Saves state to strings.json after every action
- Keyboard shortcuts: O (open+copy), N (done+next), S (skip)

## URL Parsing Logic

```python
Input                                          → (type, slug)
"twentyten"                                    → ("wp-themes", "twentyten")
"wp-plugins/woocommerce"                       → ("wp-plugins", "woocommerce")
".../projects/wp-themes/twentyten/ml/default/" → ("wp-themes", "twentyten")
".../locale/ml/default/wp-themes/twentyten/"   → ("wp-themes", "twentyten")
".../locale/ml/default/wp-themes/?filter=..."  → ERROR (listing page)
```

## Translation Quality

All quality control is in `context/prompt-template.md`:
- Strict rules (no English, natural flow, preserve format)
- Mandatory glossary table
- Style guide per context type
- Good/bad examples
- Format preservation examples
- Common mistakes table

This file is embedded in every generated prompt, ensuring consistent quality regardless of which AI agent does the translation.
