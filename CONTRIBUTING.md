# Contributing

Thank you for your interest in improving Automated Book Publication Workflow!

Contributions of code, documentation, bug reports, tests, and feature ideas are welcome.

## Before You Start

- Check existing [issues](https://github.com/AvinabhDutta-Dev/book-publication-workflow/issues) to see whether the problem or idea has already been discussed.
- For a significant change, open an issue first so we can discuss the approach.
- For small documentation fixes, you can submit a pull request directly.

## Development Setup

1. Fork this repository on GitHub.
2. Clone your fork:

   ```bash
   git clone https://github.com/YOUR-USERNAME/book-publication-workflow.git
   cd book-publication-workflow
   ```

3. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   ```

   Windows PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   macOS/Linux:

   ```bash
   source .venv/bin/activate
   ```

4. Install dependencies and the Chromium browser:

   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   playwright install chromium
   ```

5. Copy `.env.example` to `.env` and add your own Gemini API key.

   Never commit your `.env` file, API keys, or other secrets.

## Making Changes

- Keep changes focused and explain their purpose.
- Preserve the meaning of source text when improving the writing workflow.
- Update documentation when behavior or setup instructions change.
- Add or update tests when possible.
- Do not commit generated outputs or personal credentials unless they are intentionally required.

## Submitting a Pull Request

1. Create a branch for your change.
2. Make and verify your changes locally.
3. Commit your work with a descriptive message.
4. Push the branch to your fork.
5. Open a pull request against the `main` branch of this repository.

In your pull request, explain:
- What changed and why.
- How you tested the change.
- Any limitations, configuration changes, or other considerations.

Please be respectful and constructive when discussing suggestions or reviewing contributions.

Thank you for helping improve this project!
