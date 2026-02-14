# Valentine Crossword

This is a static, mobile-first crossword web app designed to be deployable on GitHub Pages.

## Local Preview

Because Node is currently broken on this machine, run a simple static server if available:

```bash
python3 -m http.server 8080
```

Then open `http://localhost:8080`.

## Deploy to GitHub Pages

1. Create a GitHub repo and push this folder.
2. In GitHub: `Settings -> Pages`.
3. Set `Source` to `Deploy from a branch`.
4. Choose branch `main` and folder `/ (root)`.
5. Save. GitHub will publish a URL.

## Current State

- Includes a fully crossed final puzzle in `src/puzzle.js`.
- Uses your themed entries plus filler entries with across/down clues.
- UI supports mobile interaction, typing, cell selection, direction switching, check/reveal/clear, and timer.
