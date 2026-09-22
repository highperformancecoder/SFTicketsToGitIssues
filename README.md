# SFTicketsToGitIssues

Python script to automate the migration of SourceForge tickets to GitHub Issues.

## Features

- Fetches tickets from SourceForge projects using the REST API
- Creates corresponding issues in GitHub repositories
- Preserves original ticket metadata (reporter, dates, status)
- **Migrates discussion threads and comments as GitHub issue comments**
- **Includes attachments with links to original SourceForge files**
- **Embeds image attachments directly in GitHub issues**
- **Imports SourceForge labels/tags as GitHub labels (preserving original names)**
- Supports filtering by ticket status (open, closed, or all)
- Includes dry-run mode for testing
- Configurable via command-line arguments or JSON config file
- Rate limiting to respect API limits, with automatic wait-and-retry when GitHub throttles requests
- Resumable: progress is saved to a state file, so an interrupted run can pick up where it left off
- Comprehensive logging

## Requirements

- Python 3.8 or higher
- GitHub personal access token with `repo` permissions
- SourceForge project with accessible tickets

## Installation

1. Clone this repository:
```bash
git clone https://github.com/highperformancecoder/SFTicketsToGitIssues.git
cd SFTicketsToGitIssues
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### Option 1: Configuration File

Create a `config.json` file (see `config.example.json`):

```json
{
  "sf_project": "your-sourceforge-project",
  "sf_tracker": "bugs",
  "gh_owner": "your-github-username",
  "gh_repo": "your-repository-name",
  "gh_token": "your-github-personal-access-token",
  "issue_delay": 2.0,
  "comment_delay": 1.0,
  "max_retries": 5,
  "state_file": "migration_state.json"
}
```

### Option 2: Command-Line Arguments

Pass configuration directly via command-line arguments (see Usage below).

### Option 3: Environment Variable

Set your GitHub token as an environment variable:
```bash
export GITHUB_TOKEN="your-github-personal-access-token"
```

## Usage

### Basic Usage

Migrate all open tickets using a config file:
```bash
python sf_tickets_to_github.py --config config.json
```

Migrate using command-line arguments:
```bash
python sf_tickets_to_github.py \
  --sf-project myproject \
  --gh-owner myusername \
  --gh-repo myrepo \
  --gh-token YOUR_TOKEN
```

### Advanced Options

Dry run (test without creating issues):
```bash
python sf_tickets_to_github.py --config config.json --dry-run
```

Migrate only a limited number of tickets:
```bash
python sf_tickets_to_github.py --config config.json --limit 5
```

Migrate closed tickets:
```bash
python sf_tickets_to_github.py --config config.json --status closed
```

Migrate all tickets (open and closed):
```bash
python sf_tickets_to_github.py --config config.json --status all
```

Verbose logging:
```bash
python sf_tickets_to_github.py --config config.json --verbose
```

Slow down issue/comment creation (e.g. if GitHub is rate-limiting you):
```bash
python sf_tickets_to_github.py --config config.json --issue-delay 5 --comment-delay 3
```

Resuming after an interruption or error is automatic — just re-run the same command. The
script tracks completed tickets in a state file (default `migration_state.json`) and skips
them on the next run:
```bash
python sf_tickets_to_github.py --config config.json
# ... GitHub rate limit hit, migration stops after saving progress ...
python sf_tickets_to_github.py --config config.json
# ... resumes from where it left off ...
```

### Command-Line Options

```
  --config CONFIG       Path to JSON configuration file
  --sf-project PROJECT  SourceForge project name
  --sf-tracker TRACKER  SourceForge tracker name (default: bugs)
  --gh-owner OWNER      GitHub repository owner
  --gh-repo REPO        GitHub repository name
  --gh-token TOKEN      GitHub personal access token
  --status {open,closed,all}
                        Status of tickets to migrate (default: open)
  --limit LIMIT         Maximum number of tickets to migrate
  --dry-run             Don't actually create issues, just show what would be done
  --issue-delay SECONDS   Seconds to wait after creating each GitHub issue (default: 2.0)
  --comment-delay SECONDS Seconds to wait after adding each GitHub comment (default: 1.0)
  --max-retries N       Max times to wait out a GitHub rate limit before aborting (default: 5)
  --state-file PATH     File used to track migration progress for resuming (default: migration_state.json)
  --verbose, -v         Verbose output
```

## How It Works

1. **Fetching Tickets**: The script uses the SourceForge REST API to fetch tickets from the specified project and tracker.

2. **Fetching Details**: For each ticket, the script fetches detailed information including discussion threads and attachments.

3. **Converting Format**: Each SourceForge ticket is converted to GitHub issue format:
   - Title: `[SF#<ticket_num>] <original_summary>`
   - Body: Contains metadata (reporter, dates, status), original description, embedded images, and attachment links
   - Labels: Automatically tagged with `migrated-from-sourceforge`, status labels (`sf-status-*`), and SourceForge tags/labels (preserving original names)
   - Comments: Discussion thread posts are added as GitHub issue comments

4. **Creating Issues**: Issues are created in the GitHub repository using the GitHub API.

5. **Adding Comments**: Each comment from the SourceForge discussion thread is added to the GitHub issue with attribution.

6. **Rate Limiting**: The script waits between API calls (`--issue-delay`/`--comment-delay`) to
   avoid triggering rate limits in the first place. If GitHub still responds with a rate-limit
   status (403/429), the script automatically waits the time GitHub requests (from the
   `Retry-After` or `X-RateLimit-Reset` headers, falling back to 60s) and retries, up to
   `--max-retries` times.

7. **Resuming**: After each ticket is fully migrated (issue + comments), its ticket number is
   saved to the state file (`--state-file`). If the script has to stop — because retries were
   exhausted, or GitHub returned some other unrecoverable error — it exits with a non-zero
   status and logs which ticket it stopped on. Re-running the same command skips tickets already
   recorded in the state file and continues from there.

## GitHub Token Permissions

Your GitHub personal access token needs the following permissions:
- `repo` (Full control of private repositories) - Required to create issues

To create a token:
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select the `repo` scope
4. Generate and copy the token

## Limitations

- Attachment files themselves are not uploaded to GitHub (only links to SourceForge are provided due to API limitations)
- The script does not close GitHub issues based on SourceForge ticket status (they are created as open)
- Rate limits apply to both SourceForge and GitHub APIs

## Troubleshooting

**"Error fetching tickets"**: Check that your SourceForge project name and tracker name are correct.

**"Error creating issue"**: Verify your GitHub token has the correct permissions and is not expired.

**Rate limiting**: The script automatically waits out GitHub rate limits and retries (up to `--max-retries` times). If it still can't proceed, it stops and saves progress to the state file — increase `--issue-delay`/`--comment-delay` and simply re-run the same command to resume.

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
