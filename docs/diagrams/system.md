# DocRunner — System Diagrams

## C4 — Component / pipeline

```mermaid
flowchart TD
    User([User / Client])
    CLI[CLI<br/>docrunner]
    API[REST API<br/>FastAPI /scrape]

    subgraph Core[DocRunner Core]
        ORCH[Orchestrator<br/>scrape url]
        CLS[Classifier<br/>detect_source]
        subgraph Fetch[Fetch Layer]
            HTTP[http.fetch]
            GD[gdrive resolver]
        end
        subgraph Extract[Extractors]
            EH[html → md]
            EP[pdf → md]
            ED[docx → md]
            ET[text passthrough]
        end
        RES[ScrapeResult<br/>markdown + title + links]
    end

    Web[(Websites)]
    Drive[(Google Drive / Docs)]

    User --> CLI --> ORCH
    User --> API --> ORCH
    ORCH --> CLS
    CLS -->|webpage / file| HTTP
    CLS -->|drive / docs| GD --> HTTP
    HTTP --> Web
    HTTP --> Drive
    HTTP -->|bytes + content-type| ORCH
    ORCH -->|dispatch by kind| EH & EP & ED & ET
    EH & EP & ED & ET --> RES
    RES --> CLI
    RES --> API
```

## Sequence — scrape a Google Docs link

```mermaid
sequenceDiagram
    actor U as User
    participant O as Orchestrator
    participant C as Classifier
    participant G as gdrive resolver
    participant H as http.fetch
    participant E as html extractor

    U->>O: scrape("docs.google.com/document/d/ID/edit")
    O->>C: detect_source(url)
    C-->>O: GDOCS
    O->>G: resolve(url)
    G-->>O: export URL (?format=html)
    O->>H: fetch(export URL)
    H-->>O: FetchedContent(html bytes)
    O->>E: to_markdown(content)
    E-->>O: ScrapeResult(markdown, title)
    O-->>U: markdown
```

## Sequence — webpage with linked PDF (include_linked_docs)

```mermaid
sequenceDiagram
    actor U
    participant O as Orchestrator
    participant H as http.fetch
    participant EH as html extractor
    participant EP as pdf extractor

    U->>O: scrape(page, include_linked_docs=true)
    O->>H: fetch(page)
    H-->>O: html bytes
    O->>EH: to_markdown(html)
    EH-->>O: ScrapeResult + links[]
    loop each PDF/DOCX link (best-effort)
        O->>H: fetch(doc link)
        H-->>O: bytes
        O->>EP: to_markdown(bytes)
        EP-->>O: section markdown
    end
    O-->>U: combined markdown (## Linked documents)
```

## State — source classification & re-classification

```mermaid
stateDiagram-v2
    [*] --> Classify
    Classify --> GDOCS: docs.google.com
    Classify --> GDRIVE: drive.google.com
    Classify --> WEBPAGE: html host
    Classify --> DIRECTFILE: .pdf/.docx ext
    GDOCS --> Fetch
    GDRIVE --> Fetch
    WEBPAGE --> Fetch
    DIRECTFILE --> Fetch
    Fetch --> Reclassify: content-type sniff
    Reclassify --> HTML
    Reclassify --> PDF
    Reclassify --> DOCX
    Reclassify --> TEXT
    HTML --> [*]
    PDF --> [*]
    DOCX --> [*]
    TEXT --> [*]
```
