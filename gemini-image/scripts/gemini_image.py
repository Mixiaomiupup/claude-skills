#!/usr/bin/env python3
"""Gemini image generation and understanding via Vertex AI.

Usage:
    # Generate image
    python gemini_image.py generate "A cute cat on a book" --output /tmp/cat.png

    # Understand image
    python gemini_image.py understand /path/to/image.png "What is in this image?"

    # Edit image (provide source image + edit instruction)
    python gemini_image.py edit /path/to/image.png "Add sunglasses to the cat" --output /tmp/edited.png
"""

import argparse
import os
import sys
from io import BytesIO
from pathlib import Path

from google import genai
from google.genai.types import GenerateContentConfig, Modality, Part
from google.oauth2 import service_account
from PIL import Image

SERVICE_ACCOUNT_FILE = os.path.expanduser(
    "~/uxfv3f-ogqz-cc08ce285c88.json"
)
PROJECT = "uxfv3f-ogqz"
LOCATION = "us-central1"
IMAGE_GEN_MODEL = "gemini-2.0-flash-preview-image-generation"
IMAGE_UNDERSTAND_MODEL = "gemini-2.5-flash"


def get_client() -> genai.Client:
    """Create authenticated Gemini client."""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    return genai.Client(
        vertexai=True,
        project=PROJECT,
        location=LOCATION,
        credentials=credentials,
    )


def generate_image(prompt: str, output_path: str) -> None:
    """Generate an image from a text prompt."""
    client = get_client()
    response = client.models.generate_content(
        model=IMAGE_GEN_MODEL,
        contents=prompt,
        config=GenerateContentConfig(
            response_modalities=[Modality.TEXT, Modality.IMAGE],
        ),
    )
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    for part in response.candidates[0].content.parts:
        if part.text:
            print(part.text)
        elif part.inline_data:
            image = Image.open(BytesIO(part.inline_data.data))
            image.save(output_path)
            print(f"Image saved: {output_path} ({image.size[0]}x{image.size[1]})")


def understand_image(image_path: str, prompt: str) -> None:
    """Analyze an image with a text prompt."""
    client = get_client()
    img = Image.open(image_path)
    buf = BytesIO()
    fmt = "PNG" if image_path.lower().endswith(".png") else "JPEG"
    img.save(buf, format=fmt)
    image_bytes = buf.getvalue()
    mime = "image/png" if fmt == "PNG" else "image/jpeg"

    response = client.models.generate_content(
        model=IMAGE_UNDERSTAND_MODEL,
        contents=[
            prompt,
            Part.from_bytes(data=image_bytes, mime_type=mime),
        ],
    )
    print(response.text)


def edit_image(image_path: str, prompt: str, output_path: str) -> None:
    """Edit an image based on a text instruction."""
    client = get_client()
    img = Image.open(image_path)
    buf = BytesIO()
    fmt = "PNG" if image_path.lower().endswith(".png") else "JPEG"
    img.save(buf, format=fmt)
    image_bytes = buf.getvalue()
    mime = "image/png" if fmt == "PNG" else "image/jpeg"

    response = client.models.generate_content(
        model=IMAGE_GEN_MODEL,
        contents=[
            prompt,
            Part.from_bytes(data=image_bytes, mime_type=mime),
        ],
        config=GenerateContentConfig(
            response_modalities=[Modality.TEXT, Modality.IMAGE],
        ),
    )

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    for part in response.candidates[0].content.parts:
        if part.text:
            print(part.text)
        elif part.inline_data:
            image = Image.open(BytesIO(part.inline_data.data))
            image.save(output_path)
            print(f"Image saved: {output_path} ({image.size[0]}x{image.size[1]})")


def main():
    parser = argparse.ArgumentParser(description="Gemini image tools")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate image from text")
    gen.add_argument("prompt", help="Text prompt")
    gen.add_argument("--output", "-o", default="/tmp/gemini_output.png")

    und = sub.add_parser("understand", help="Analyze an image")
    und.add_argument("image", help="Path to image file")
    und.add_argument("prompt", nargs="?", default="Describe this image in detail.")

    edit = sub.add_parser("edit", help="Edit an image with instructions")
    edit.add_argument("image", help="Path to source image")
    edit.add_argument("prompt", help="Edit instruction")
    edit.add_argument("--output", "-o", default="/tmp/gemini_edited.png")

    args = parser.parse_args()

    if args.command == "generate":
        generate_image(args.prompt, args.output)
    elif args.command == "understand":
        understand_image(args.image, args.prompt)
    elif args.command == "edit":
        edit_image(args.image, args.prompt, args.output)


if __name__ == "__main__":
    main()
