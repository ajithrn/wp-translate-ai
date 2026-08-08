# Architecture — wp-translate-ai

Technical documentation for the internal system design of **`wp-translate-ai`**.

---

## System Design

```mermaid
graph TD
    CLI["wp-translate-ai.py<br/>(CLI router)"]

    CLI --> init
    CLI --> add_locale["add-locale / create-locale"]
    CLI --> fetch
    CLI --> fetch_glossary["fetch-glossary"]
    CLI --> translate
    CLI --> apply
    CLI --> submit
    CLI --> config["config.json<br/>lib/config.py"]

    init --> terminal["Interactive terminal"]
    add_locale --> glossary["lib/glossary.py<br/>(init_locale)"]
    fetch --> fetcher["lib/fetcher.py"]
    fetch_glossary --> glossary
    translate --> translator["lib/translator.py"]
    apply --> translator
    submit --> submitter["lib/submitter.py"]

    fetcher --> glotpress["GlotPress<br/>(scrape)"]
    glossary --> glotpress_glossary["GlotPress Glossary<br/>(export & scrape)"]
    translator --> context["context/prompt-template.md &<br/>context/locales/&lt;locale&gt;/"]
    translator --> datadir["data/&lt;slug&gt;/&lt;locale&gt;/<br/>strings.json"]
    submitter --> browser["Browser<br/>localhost:8787"]
```

---

## Data Flow (Overview)

```mermaid
flowchart LR
    A["URL / Slug / --locale"] --> B["Add Locale & Fetch"]
    B --> C["Translate"]
    C --> D["AI IDE Agent"]
    D --> E["Apply"]
    E -->|"repeat"| C
    E --> F["Submit Helper"]
```

---

## Data Flow (Detailed)

```mermaid
flowchart TD
    start(["User gives URL or slug"]) --> fetch

    subgraph fetch["FETCH & LOCALE INIT"]
        direction TB
        f0["Auto-init locale context if missing<br/>(context/locales/locale/)"]
        f1["Parse URL & resolve locale"]
        f2["Call GlotPress API for stats"]
        f3["Scrape HTML pages for<br/>pending strings"]
        f4[("data/slug/locale/strings.json")]
        f0 --> f1 --> f2 --> f3 --> f4
    end

    fetch --> translate

    subgraph translate["TRANSLATE"]
        direction TB
        t1["Load pending strings<br/>from data/slug/locale/strings.json"]
        t2["Select next batch of N"]
        t_ctx[/"context/prompt-template.md &<br/>context/locales/locale/prompt-template.md"/]
        t3["Assemble full prompt:<br/>global rules + locale rules + glossary + strings"]
        t4[("data/slug/locale/prompt.md")]
        t1 --> t2 --> t3 --> t4
        t_ctx --> t3
    end

    translate --> userai

    subgraph userai["USER + AI AGENT"]
        direction TB
        u1["AI Agent reads prompt.md"]
        u2["AI generates target language<br/>translations as JSON"]
        u3[("data/slug/locale/response.json")]
        u1 --> u2 --> u3
    end

    userai --> apply

    subgraph apply["APPLY"]
        direction TB
        a1["Load data/slug/locale/response.json"]
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

---

## Per-Project Data (`data/<slug>/<locale>/`)

Each project and locale combination gets its own scoped directory:

```text
data/
├── twentyten/
│   ├── ml/
│   │   ├── strings.json           # Main project data for Malayalam
│   │   ├── prompt.md              # Latest generated AI prompt (gitignored)
│   │   ├── response.json          # AI output before apply (gitignored)
│   │   └── response_applied.json  # Archived after apply (gitignored)
│   └── hi/
│       └── strings.json           # Main project data for Hindi
├── gutenberg/
│   └── stable/
│       └── ml/
│           └── strings.json
└── woocommerce/
    └── hi/
        └── strings.json
```

---

## Modular Locale Architecture (`context/locales/`)

Rules and glossaries are decoupled per locale:

```text
context/
├── prompt-template.md         # Global technical & placeholder rules
└── locales/
    ├── ml/
    │   ├── prompt-template.md # Native register & Malayalam style guide
    │   └── glossary.json      # Auto-fetched GlotPress official terms
    └── hi/
        ├── prompt-template.md # Native register & Hindi style guide
        └── glossary.json      # Auto-fetched GlotPress official terms
```

---

## Components

### Configuration (`config.json` & `lib/config.py`)
- Reads global settings (`default_locale`, `default_batch_size`, `user_agent`).
- Resolves CLI `--locale` arguments and fallback values.

### Fetcher (`lib/fetcher.py`)
- Scrapes pending strings from any GlotPress project.
- Automatically discovers nested sub-projects (e.g. `gutenberg/stable`).

### Glossary Manager (`lib/glossary.py`)
- Fetches official GlotPress glossaries for any target locale.
- Stores terms locally as `context/locales/<locale>/glossary.json`.

### Translator (`lib/translator.py`)
- Generates `prompt.md` using the target locale template and official glossary.
- Parses AI response JSON and updates `strings.json`.

### Submitter (`lib/submitter.py`)
- Embedded single-page HTML submit app (zero dependencies).
- Runs HTTP server on `http://localhost:8787`.
- Updates submission progress in `strings.json`.

