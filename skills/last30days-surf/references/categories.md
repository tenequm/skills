# Category peers

Topic-to-peer-subreddits lookup for entity resolution. First-match-wins on compound substrings; bare common nouns are forbidden (no `image` / `ai` / `model` matches).

This table extends the WebSearch-extracted subreddit list during Step 0.5 entity resolution. WebSearch hits always win over peers; peers fill in known communities.

## CATEGORY_PEERS table

```
ai_image_generation:
  patterns: image generation, image gen, text to image, text-to-image, gpt image, gpt-image, nano banana, midjourney, stable diffusion, stablediffusion, dall-e, dalle, flux.1, flux schnell, imagen, seedance, ideogram, recraft
  peers:    StableDiffusion, midjourney, dalle2, aiArt, PromptEngineering, MediaSynthesis

ai_video_generation:
  patterns: video generation, text to video, text-to-video, sora, veo 3, veo3, runway gen, kling, pika labs, luma dream machine, hailuo
  peers:    aivideo, StableDiffusion, runwayml, singularity, MediaSynthesis

ai_music_generation:
  patterns: music generation, ai music, suno, udio, riffusion, stable audio
  peers:    SunoAI, udiomusic, aimusic, artificial

ai_coding_agent:
  patterns: claude code, cursor ide, github copilot, windsurf, aider, cline, continue.dev, codeium, sweep ai, devin ai, coding agent, coding assistant
  peers:    ChatGPTCoding, LocalLLaMA, singularity, PromptEngineering

ai_agent_framework:
  patterns: agent framework, agentic framework, langchain, langgraph, crewai, autogen, llamaindex, dspy, smolagents
  peers:    LangChain, LocalLLaMA, AI_Agents, MachineLearning

ai_chat_model:
  patterns: gpt-5, gpt-4, claude opus, claude sonnet, claude haiku, gemini pro, gemini flash, llama 3, llama 4, deepseek, qwen, mistral large, grok
  peers:    LocalLLaMA, ChatGPT, ClaudeAI, singularity, artificial

saas_screen_recording:
  patterns: screen recording, screen recorder, loom video, tella screen, vidyard, screen capture tool
  peers:    SaaS, screenrecording, productivity, Entrepreneur

saas_productivity:
  patterns: notion app, obsidian plugin, obsidian app, linear app, asana, clickup, productivity app
  peers:    productivity, SaaS, ObsidianMD, Notion

prediction_markets:
  patterns: polymarket, kalshi, prediction market, event contracts, manifold markets
  peers:    Polymarket, Kalshi, predictionmarkets

crypto_defi:
  patterns: defi protocol, yield farming, liquidity pool, stablecoin, ethereum layer, layer 2, l2 rollup
  peers:    defi, ethfinance, CryptoCurrency, ethereum

dev_tool_cli:
  patterns: cli tool, command line tool, terminal app, dev tool
  peers:    commandline, programming, webdev
```

## Rules

- **First match wins.** Order matters — `ai_image_generation` is checked before `ai_chat_model` so "gpt image 2" routes to image-gen peers, not chat-model peers.
- **No bare common nouns.** Patterns are compound terms or domain-specific tokens to avoid false positives.
- **Case-insensitive substring** match against the topic.
- **Cap at 10 total subs** (WebSearch hits + peers, deduped case-insensitively, WebSearch retained).

## Generic-handle deny-list (used in handle resolution)

```
elonmusk, openai, google, microsoft, apple, meta, github, youtube, x,
twitter, reddit, wikipedia, nytimes, washingtonpost, cnn, bbc, reuters,
verified, jack, sundarpichai
```

These crowd out topic-specific voices in `@handle` frequency rankings — drop them when picking the top X handle for a topic.

## Skip-owner list (GitHub URL extraction)

```
topics, explore, settings, orgs, search, features, about, pricing, enterprise
```

Without these, `github.com/topics/ai` would parse as a fake "topics" user.

## Utility-subreddit penalty (Reddit subreddit ranking)

Apply `0.3x` penalty to subreddit relevance score when the subreddit is one of:

```
namethatsong, tipofmytongue, findareddit, AskReddit (when not topic-relevant),
NoStupidQuestions, OutOfTheLoop, explainlikeimfive (when not eli5-mode)
```

Plus `+2.0` boost when the subreddit name contains a core topic word, and `+0.5` if any post in that sub had >100 upvotes.
