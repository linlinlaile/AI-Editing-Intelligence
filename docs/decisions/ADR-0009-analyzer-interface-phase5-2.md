# ADR-0009: Phase 5.2 Analyzer Interface

- Status: Accepted
- Date: 2026-09-12

Analyzer receives Artifact, Sample, and future audio-segment references through AnalysisInput, receives run and producer provenance through AnalyzerContext, and returns both Observation and Evidence in AnalysisResult. It does not access a repository. The application layer validates and persists results. Existing storage tables are reused; no migration or model provider is added.
