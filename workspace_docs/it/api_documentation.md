# Internal API Documentation

## Overview
This document describes the REST API exposed by the retrieval platform. It is maintained by the Infrastructure team and is intended for backend engineers integrating with the search and ingestion services.

## Base URL
All endpoints are served under /api and return JSON unless otherwise noted.

## Endpoints

### GET /api/search
Runs a context-aware search across indexed documents.
Query parameters:
- q (string, required): the search query
- department (string, optional): filter by department
- file_type (string, optional): filter by file extension
- page (int, optional): pagination page number
- per_page (int, optional): results per page (default 10)

### GET /api/suggest
Returns autocomplete suggestions from the trie index.
Query parameters:
- prefix (string, required): the partial query typed by the user

### POST /api/ingest
Triggers ingestion of the workspace folder. Returns a summary of indexed, updated, and skipped files.

### GET /api/analytics
Returns dashboard metrics: total documents, total searches, top queries, and most accessed documents.

## Authentication
Internal endpoints assume a trusted network. For production, place the service behind SSO and enforce per-department access rules.

## Rate Limiting
Search endpoints are limited to 60 requests per minute per user to protect the database during peak load.

## Error Handling
Errors return a JSON body with an error code and human-readable message. A 404 indicates no matching document; a 429 indicates rate limiting.

Maintained by: Usman Tariq, Platform Engineer, Infrastructure
