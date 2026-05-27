"""MCP/API Gateway — drop-in OpenAI-compatible proxy with auditing.

Second collector of the Heillon substrate. Users repoint their existing
OpenAI/Anthropic-compatible client to this gateway by changing ONE config
value (base URL). All AI calls then transparently:

  1. Authenticate via X-Heillon-Api-Key (Heillon API key)
  2. Forward to upstream (default api.openai.com) with X-Upstream-Api-Key
  3. Return the upstream response verbatim
  4. Generate an HDR asynchronously (background task) with prompt + response

Supports any OpenAI Chat Completions-compatible endpoint: OpenAI, Together,
Anyscale, Groq, DeepSeek, Mistral, vLLM, Ollama, etc.
"""
