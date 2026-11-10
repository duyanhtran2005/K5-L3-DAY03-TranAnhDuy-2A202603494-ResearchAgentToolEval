---
name: lookup
track: core
kind: live_api
provider: Tavily
requires_env: [TAVILY_API_KEY]
inputs: [query, topic, timeframe, max_results]
outputs: [items]
side_effect: false
---
# lookup

Searches the web via Tavily. Has a `topic` (`general` or `news`) and a
`timeframe` argument.

## Input boundary regression

max_results must be positive. Zero and negative values return a ValueError
dictionary before HTTP; integer strings such as "3" remain supported.
