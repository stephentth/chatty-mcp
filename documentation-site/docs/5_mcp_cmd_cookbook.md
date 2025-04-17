---
sidebar_position: 5
title: MCP Commandline Cookbook
---

# MCP Commandline Cookbook

## Using Kokoro streaming

```
uv tool run chatty.py --engine kokoro --stream
```

## Using normal mode

Can be slow

```
uv tool run chatty.py --engine kokoro
```

## System built-in TTS

```
uv tool run chatty.py --engine system
```

## Test

Run a test voice and exist to debug what can go wrong

```
uv run chatty.py --engine kokoro --stream --test-voice kokoro
```

## Help

```
uv run chatty.py --help
```
