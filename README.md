# Hi.

Oh.

You're here.

Give me a second. I was doing something.

<p align="center">
  <a href="https://ayeshamashiat.github.io/ayeshamashiat/desktop.svg">
    <img src="assets/desktop.svg?v=6" width="100%" alt="Ayesha's desktop: a terminal with six folders: coding, reading, making cha, ML rabbit hole, nuclear accidents and questionable decisions. 17 tabs are open. 4 of them are important. She doesn't know which 4.">
  </a>
</p>

<p align="center"><sub>the folders actually open. just not here, github won't let an image do anything fun. <a href="https://ayeshamashiat.github.io/ayeshamashiat/desktop.svg">here's the real one.</a></sub></p>

### ⌁ Anyway.

I'm **Ayesha**.

I build software, mostly backend stuff, and lately I've been getting curious about **how AI actually works**.

The backend part is going well. The AI part is a rabbit hole. There's a folder for it.

<img src="assets/h-built.svg?v=3" width="100%" alt="Things I've built">

<sub><code>01</code></sub>

### [Bouncer](https://github.com/ayeshamashiat/Bouncer)

A security gate for AI agents. Before one installs a third-party skill, Bouncer checks it against a **threat graph** and answers `ALLOW`, `ASK` or `BLOCK`.

`FastAPI` `FalkorDB` `React` `Cytoscape.js` `MCP` `Claude Code hooks`

Blocklists only catch what's already known. So instead of listing bad skills, it maps how accounts, domains, IPs and payloads connect.

```text
skill → shared infrastructure → known malware
2 hops = BLOCK · 3-4 hops = ASK
```

Weakly connected components cluster reports into campaigns automatically. **92%** detection on hidden malware, versus **0%** for a plain blocklist. Suspicious instructions are read without ever being executed.

<sub><code>02</code></sub>

### [Touch Grass, Babu](https://github.com/ayeshamashiat/Touch-Grass-Babu)

An Android app where an AI mom roasts you for doomscrolling, then locks the app until you go outside.

`Kotlin` `llama.cpp (NDK)` `LoRA` `GGUF` `ML Kit` `WorkManager`

A fine-tuned **Qwen 3.5-4B**, quantized and running **fully offline** on the phone. The app has no internet permission.

```text
3,700-token prompt → distilled into the weights → 4B model → phone
```

Roasts are pre-generated while charging, and on-device vision checks your photo for sky and grass.

<sub><code>03</code></sub>

### [PetniHunter](https://github.com/ayeshamashiat/PetniHunter)

A hallucination guard for a **Bangla** language model. Ask about a writer who doesn't exist and it refuses.

`Python` `Qwen3.5-4B` `Wikidata` `bn.wikipedia`

```text
question → (entity, property) → spelling-tolerant search
         → title similarity → Wikidata type check
         → refuse · redirect · rescue
```

**91.9 F-score** on 2,367 test items with **0.1%** false acceptances. It never silently swaps in a similar name, and it can tell "not found" from "network down".

<sub><code>04</code></sub>

### [AgriSense](https://github.com/ayeshamashiat/CommittedToConflict_AgriSense)

An autonomous farming advisor for smallholder farmers in Bangladesh.

`FastAPI` `ChromaDB` `RAG` `Tool-calling agent` `React` `Web Speech API`

An agent with a tool registry (weather, finance, irrigation, pest risk, marketplace, disease detection) and persistent farmer memory.

**The LLM writes the words. The tools produce every number.** Weather alerts shift the real season plan, it works in Bengali by voice, and every estimate says how uncertain it is.

<sub>Older work: [CareerPilot](https://github.com/ayeshamashiat/CareerPilor_CodeSprint) (RAG career assistant) · [Jobscape](https://github.com/ayeshamashiat/Jobscape_Backend) (FastAPI, PostgreSQL, spaCy) · [PAMS](https://github.com/ayeshamashiat/PAMS_Backend) (Node, MongoDB, RBAC thesis workflow)</sub>

<img src="assets/h-rabbit-hole.svg?v=3" width="100%" alt="The current rabbit hole">

## Machine learning

I'm pretty new to it. Right now I'm learning the fundamentals and trying to understand what's actually happening, rather than immediately reaching for a library.

For example:

```python
model.fit(X, y)
```

I'd like to know what that line is actually doing.

```text
linear regression    ▰▰▰▰▰▰▱▱▱▱
gradient descent     ▰▰▰▰▰▱▱▱▱▱
classification       ▰▰▰▱▱▱▱▱▱▱
neural networks      ▰▱▱▱▱▱▱▱▱▱
```

Very much a work in progress.

**Next rabbit holes:** `RAG` · `LangChain` · `LangGraph` · `LLM workflows` · `Agents`

<img src="assets/h-toolbox.svg?v=3" width="100%" alt="My toolbox">

<img src="assets/toolbox.svg" width="100%" alt="Toolbox: Python, JavaScript, SQL; FastAPI, Node.js, Express; PostgreSQL, MongoDB, MySQL; NumPy, scikit-learn, spaCy, Sentence Transformers; Docker, AWS, Nginx, GitHub Actions.">

<img src="assets/h-contributions.svg?v=3" width="100%" alt="My contributions">

<p align="center">
  <img src="assets/pokeballs.svg?v=2" width="100%" alt="Ayesha's GitHub contributions over the last year. Each day is a Pokéball, and busier days get a different colour of ball. Days with no contributions are empty grass.">
</p>

One Pokéball for every day I pushed something. The busier the day, the fancier the ball. Empty grass is a day I didn't. It redraws every night.

<img src="assets/h-status.svg?v=3" width="100%" alt="Status report">

<img src="assets/status.svg?v=3" width="100%" alt="17+ repositories. 3 hackathon finals. 1 top 100. Top 100: Solvio AI Hackathon 2025. Finalist: CodeSprint, Inter-IUT Hackathon, top 14 among top 50. Finalist: SUST CSE Carnival Hackathon, top 50 among 450+ submissions. Finalist: IUT 12th ICT Fest, Agentic AI Hackathon, top 20 among 700+ submissions.">

Three finalist finishes.

One Top 100 placement.

And apparently a growing collection of certificates.

<img src="assets/h-open.svg?v=3" width="100%" alt="Currently open">

<img src="assets/open.svg?v=3" width="100%" alt="Machine learning fundamentals. RAG / LLM rabbit holes. One extremely fast-paced thriller.">

One of these is going significantly better than the others.

I will not tell you which one.

<img src="assets/h-still-here.svg?v=3" width="100%" alt="You're still here">

Okay.

So either:

<p align="center">
  <img src="assets/options.svg?v=3" width="100%" alt="A) something here caught your attention. B) you clicked by accident. C) you were intrigued by my profile pic. D) you also have too many tabs open.">
</p>

Honestly, all four are valid.

If you want to talk about something I'm building, something you're building, or how I ended up reading some extremely niche historical fact at 2 AM—

<h2 align="center">say hi.</h2>

<p align="center">
  <a href="https://www.linkedin.com/in/ayesha-mashiat-89915429a/"><img src="assets/linkedin.svg?v=3" alt="LinkedIn: connect" height="44"></a>
  &nbsp;
  <a href="https://dev.to/ayeshamashiat"><img src="assets/devto.svg" alt="DEV: ayeshamashiat" height="44"></a>
  &nbsp;
  <a href="https://www.facebook.com/ayesha.mashiat"><img src="assets/facebook.svg?v=3" alt="Facebook: find me" height="44"></a>
  &nbsp;
  <a href="https://instagram.com/_.ayshiat._"><img src="assets/instagram.svg?v=3" alt="Instagram: __.ayshiat.__" height="44"></a>
</p>

<br>

<p align="center">
  <b>Thanks for snooping around.</b><br>
  <sub>You may now return to whatever you were supposed to be doing.</sub>
</p>
