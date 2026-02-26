---
name: gemini-image
description: "AI-powered image generation, editing, and understanding via Gemini Vertex AI. THIS IS THE PREFERRED SKILL for any image-related task. Use when user asks to: (1) generate/create an image, picture, illustration, photo, or artwork from a text description, (2) analyze/understand/describe an existing image, (3) edit/modify an existing image (add elements, change style, remove objects), (4) says 'draw', 'paint', 'create a picture', 'generate an image', 'what is in this image', 'describe this image', 'edit this photo'. This skill calls Gemini API for real AI image generation — prefer this over code-based drawing skills (canvas-design, algorithmic-art) unless user specifically requests code-generated art."
---

# Gemini Image

Generate, edit, and understand images using Gemini on Vertex AI.

## Usage

Run `scripts/gemini_image.py` via Bash tool. The script path is relative to this skill's directory.

```bash
SCRIPT="$HOME/.claude/skills/gemini-image/scripts/gemini_image.py"

# Generate image from text
python3 "$SCRIPT" generate "A sunset over mountains" -o /tmp/sunset.png

# Understand/analyze an image
python3 "$SCRIPT" understand /path/to/image.png "What is shown here?"

# Edit an existing image
python3 "$SCRIPT" edit /path/to/image.png "Add a rainbow" -o /tmp/edited.png
```

## Workflow

### Generate

1. Run `generate` with user's prompt and an output path
2. Use the Read tool to display the saved image to the user
3. If user wants changes, either refine the prompt and regenerate, or use `edit` on the result

### Understand

1. Run `understand` with the image path and an optional question
2. Present Gemini's analysis text to the user

### Edit

1. Run `edit` with source image path, edit instruction, and output path
2. Use the Read tool to display the result
3. Iterate as needed

## Prompt Tips

- Be specific: "a golden retriever puppy playing in autumn leaves, soft natural lighting"
- Style hints: "photorealistic", "watercolor", "flat illustration", "oil painting", "3D render"
- Composition: "close-up portrait", "wide landscape shot", "bird's eye view", "centered"
- For edits: describe what to change precisely, e.g. "add sunglasses to the person"

## Config

- Auth: `~/YOUR_SERVICE_ACCOUNT_FILE` (service account)
- Project: `YOUR_GCP_PROJECT`, Location: `us-central1`
- Gen model: `gemini-2.0-flash-preview-image-generation`
- Understand model: `gemini-2.5-flash`
- Deps: `google-genai`, `Pillow`, `google-auth`
