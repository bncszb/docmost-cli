# Docmost Skill Examples

## Example 1: Read wiki docs to inform implementation

User says: "Check the wiki for our API authentication docs"

```bash
# Search for relevant pages
docmost-cli search query "authentication" --json

# Read the page content
docmost-cli page get 019a2a69-xxxx --meta
```

## Example 2: Create documentation from code

User says: "Document the payment module in our engineering wiki"

```bash
# Create the page with generated Markdown
docmost-cli page create engineering --title "Payment Module" --content "# Payment Module

## Overview
The payment module handles all billing operations...

## API Endpoints
- POST /payments/create
- GET /payments/:id

## Configuration
Set STRIPE_KEY in environment variables."
```

## Example 3: Backup all pages in a space

```bash
# Get all page IDs
docmost-cli page list engineering --json

# For each page, export to file
docmost-cli page export <page-id> --format md --output backup/<page-id>.md
```

## Example 4: Search and summarize

User says: "What does our wiki say about deployment?"

```bash
# Search
docmost-cli search query "deployment" --json

# Read each relevant result
docmost-cli page get <id-1>
docmost-cli page get <id-2>
```

Then summarize the findings for the user.

## Example 5: Create a page from a file in the repo

User says: "Publish our README to the wiki"

```bash
docmost-cli page create engineering --title "Project README" --file README.md
```

## Example 6: Browse space structure

```bash
# See the full page hierarchy
docmost-cli page list engineering --tree

# List child pages of a specific page
docmost-cli page children <parent-id> --json
```

## Example 7: Add review comments to a page

```bash
# Add a comment
docmost-cli comment create <page-id> --content "Reviewed by Claude Code - looks good, minor typo in section 3"

# List existing comments
docmost-cli comment list <page-id> --json
```
