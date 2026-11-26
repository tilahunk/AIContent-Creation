# Costs and free-tier evidence

Last checked: 2026-11-26. No external model was invoked by this project in this session. Actual model expenditure: **$0**. The previously generated preview files were made with the local mock/FFmpeg pipeline, not the models below.

Free quota and geographic eligibility can change. "Zero cost" means only that a documented free allocation may be available; it is not a guarantee of no account restrictions, no card requirement, or quota for this project. Check the provider console before production.

| Stage | Candidate | Current evidence | Cost/eligibility status |
|---|---|---|---|
| Script/TTS | Gemini API, `gemini-3.8-flash`, `gemini-3.8-flash-tts` | [Gemini API pricing](https://aistudio.google.com/docs/pricing) documents a limited free tier; [TTS guide](https://aistudio.google.com/docs/speech-generation) documents the model and `v1beta` Interactions API. | Free eligibility for the specific TTS model and Ethiopia availability were not established by the pages checked. Current [Gemini API terms](https://ai.google.dev/gemini-api/docs/terms) state unpaid-service content may be used to improve products and reviewed by humans. |
| Keyframes | Cloudflare Workers AI, `@cf/black-forest-labs/flux-1-schnell` | [Model API docs](https://developers.cloudflare.com/workers-ai/models/flux-1-schnell/) document the model and REST request. [Pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/) lists a 10,000-Neuron daily free allocation and paid usage above it. | Images-per-day depends on neuron usage per request. Cloudflare's [data-usage policy](https://developers.cloudflare.com/workers-ai/platform/data-usage/) states zero retention for standard inference and no model training, subject to exceptions. Review the model-specific terms linked from the model page. |
| Optional keyframes | FLUX.2 klein 9B | [Cloudflare model page](https://developers.cloudflare.com/workers-ai/models/flux-2-klein-9b/) lists the hosted model. | The page retrieved did not establish its exact request shape/free eligibility; adapter defaults to the documented FLUX.1 schnell JSON API. |
| Moving shots | Wan 2.2 TI2V-5B | [Official model card](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B) documents image-to-video and the repository/model card identifies Apache-2.0. | Kaggle GPU quota and successful generation were not verified. |
| Original music | ACE-Step v1.5 | [Official project page](https://ace-step.github.io/ace-step-v1.5.github.io/) documents v1.5; the [official model card](https://huggingface.co/ACE-Step/Ace-Step1.5) identifies MIT. | No generation was run. Verify licenses of any separately downloaded submodels/checkpoints and Kaggle availability before commercial use. |
| Assembly | FFmpeg | Local tool; smoke exports were verified. | $0 actual local cost. |

| Stage | Provider | Model | Actual spend | Latency/GPU minutes |
|---|---|---|---:|---|
| All current previews | Local mock + FFmpeg | Mock | $0 | External GPU minutes: 0 |

The suggested "50–170 images/day", "30 GPU hours/week", free Claude/Antigravity availability, and commercial use of music outputs were supplied by the project owner and remain **unverified**. Do not treat them as measured project results.
