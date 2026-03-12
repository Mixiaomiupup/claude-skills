---
name: gemini-image
description: "AI-powered image generation, editing, and understanding engine via Gemini Vertex AI. Use when user asks to: (1) generate/create an image from a text description, (2) analyze/understand/describe an existing image, (3) edit/modify an existing image. Triggers: 'draw', 'paint', 'create a picture', 'generate an image', 'what is in this image', 'describe this image', 'edit this photo'. For article covers and illustrations, use article-image skill instead."
---

# Gemini Image

Generate, edit, and understand images using Gemini on Vertex AI. This is the engine layer — for article covers and illustrations, use `article-image` skill.

## Script

```bash
SCRIPT="$HOME/.claude/skills/gemini-image/scripts/gemini_image.py"
```

## Modes

| Mode | Trigger | Description |
|------|---------|-------------|
| `generate` | "generate an image of..." | Free-form text → image |
| `understand` | "what is in this image" | Image → text analysis |
| `edit` | "add X to this image" | Image + instruction → edited image |

---

## Mode: generate

```bash
python3 "$SCRIPT" generate "A sunset over mountains" -o /tmp/sunset.png
```

1. Run `generate` with user's prompt and output path
2. Use Read tool to display the saved image
3. If user wants changes, refine prompt or use `edit`

**Prompt Tips**: Be specific about subject, style ("photorealistic", "watercolor", "flat illustration"), composition ("close-up", "bird's eye view"), lighting.

---

## Mode: understand

```bash
python3 "$SCRIPT" understand /path/to/image.png "What is shown here?"
```

---

## Mode: edit

```bash
python3 "$SCRIPT" edit /path/to/image.png "Add a rainbow" -o /tmp/edited.png
```

---

## Config

- Auth: `~/YOUR_SERVICE_ACCOUNT_FILE` (service account)
- Project: `YOUR_GCP_PROJECT`, Location: `us-central1`
- Gen model: `gemini-2.0-flash-preview-image-generation`
- Understand model: `gemini-2.5-flash`
- Deps: `google-genai`, `Pillow`, `google-auth`
