# Analyzer Interface

Phase 5.2 defines an infrastructure-independent analyzer boundary:

```text
AnalysisInput + AnalyzerContext
              ↓
           Analyzer
              ↓
        AnalysisResult
         ↙          ↘
 Observation       Evidence
```

`AnalysisInput` contains only identifiers for artifacts, samples, and future audio segments. It never contains a file handle, SQLite object, payload, or model client. `AnalyzerContext` contains the analysis run ID, producer reference, and configuration.

An `AnalysisResult` carries both observations and evidences so the application layer can validate run and producer provenance and ensure every Observation references Evidence before persisting it. Analyzer implementations do not write SQLite. Existing storage tables are sufficient; this phase adds no migration or table.

The Phase 5.2 fake analyzer is deterministic test infrastructure only. VLM, ASR, embedding providers, model adapters, prompts, and an analyzer registry remain out of scope.
