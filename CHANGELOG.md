# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-21

### Added

- LangGraph-based orchestrator that drives a GitHub issue through a single end-to-end pipeline run, with SQLite checkpointing (`langgraph-checkpoint-sqlite`) so paused or crashed runs can be resumed.
- Six-node pipeline covering intake → research → plan → code → verify → pr, wired as a LangGraph state machine with a verify-fail retry loop back into code (max 2 retries).
- `claude` CLI subprocess harness that invokes `claude --print` per node with a focused prompt and a slice of pipeline state, using a wall-clock timeout on every call.
- `claude-pipeline` CLI entry point with `run`, `resume`, `status`, and `graph` subcommands for starting fresh runs, resuming from checkpoint, inspecting run state, and rendering the graph as Mermaid.
