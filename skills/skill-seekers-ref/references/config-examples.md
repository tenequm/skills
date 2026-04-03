# Config Examples

Ready-to-use configurations for common frameworks. Save as JSON and use with `--config`.

## React

```json
{
  "name": "react",
  "base_url": "https://react.dev",
  "start_urls": ["https://react.dev/learn", "https://react.dev/reference"],
  "max_pages": 200,
  "rate_limit": 0.3,
  "output_dir": "output/react",
  "enhance_level": 2
}
```

## Next.js

```json
{
  "name": "nextjs",
  "base_url": "https://nextjs.org/docs",
  "start_urls": ["https://nextjs.org/docs"],
  "max_pages": 300,
  "rate_limit": 0.5,
  "output_dir": "output/nextjs",
  "enhance_level": 2
}
```

## Django (Unified - Docs + GitHub)

```json
{
  "name": "django-complete",
  "sources": [
    {
      "type": "docs",
      "base_url": "https://docs.djangoproject.com/en/5.0/",
      "max_pages": 300,
      "rate_limit": 0.5
    },
    {
      "type": "github",
      "repo": "django/django",
      "max_issues": 50,
      "include_changelog": true
    }
  ],
  "merge_mode": "rule-based",
  "output_dir": "output/django-complete",
  "enhance_level": 2
}
```

## FastAPI

```json
{
  "name": "fastapi",
  "base_url": "https://fastapi.tiangolo.com",
  "start_urls": ["https://fastapi.tiangolo.com/tutorial/"],
  "max_pages": 150,
  "rate_limit": 0.3,
  "output_dir": "output/fastapi",
  "enhance_level": 2
}
```

## Tailwind CSS (Quick Test)

```json
{
  "name": "tailwindcss",
  "base_url": "https://tailwindcss.com/docs",
  "start_urls": ["https://tailwindcss.com/docs/installation"],
  "max_pages": 50,
  "rate_limit": 0.3,
  "output_dir": "output/tailwindcss",
  "enhance_level": 1
}
```

## Local Codebase + GitHub (Unified)

```json
{
  "name": "my-project",
  "sources": [
    {
      "type": "local",
      "directory": "./src",
      "languages": ["TypeScript", "Python"],
      "preset": "comprehensive"
    },
    {
      "type": "github",
      "repo": "myorg/my-project",
      "max_issues": 100
    }
  ],
  "merge_mode": "claude-enhanced",
  "output_dir": "output/my-project",
  "enhance_level": 3
}
```

## PDF Technical Manual

```json
{
  "name": "product-manual",
  "source": "pdf",
  "pdf_path": "./docs/product-manual.pdf",
  "output_dir": "output/product-manual",
  "enhance_level": 1
}
```

## Using These Configs

```bash
# Save any example above as a JSON file
# Then run:
skill-seekers scrape --config configs/react.json
# Or with the unified command:
skill-seekers unified --config configs/django-complete.json
# Or full pipeline:
skill-seekers install --config configs/react.json
```

Skill Seekers also ships with 24 built-in presets. List them:
```bash
skill-seekers estimate --all
```
