# SFTicketsToGitIssues

Python script to automate the migration of SourceForge tickets to GitHub Issues.

## Features

- Fetches tickets from SourceForge projects using the REST API
- Creates corresponding issues in GitHub repositories
- Preserves original ticket metadata (reporter, dates, status)
- Supports filtering by ticket status (open, closed, or all)
- Includes dry-run mode for testing
- Configurable via command-line arguments or JSON config file
- Rate limiting to respect API limits
- Comprehensive logging

## Requirements

- Python 3.6 or higher
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
  "gh_token": "your-github-personal-access-token"
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
  --verbose, -v         Verbose output
```

## How It Works

1. **Fetching Tickets**: The script uses the SourceForge REST API to fetch tickets from the specified project and tracker.

2. **Converting Format**: Each SourceForge ticket is converted to GitHub issue format:
   - Title: `[SF#<ticket_num>] <original_summary>`
   - Body: Contains metadata (reporter, dates, status) and original description
   - Labels: Automatically tagged with `migrated-from-sourceforge` and status labels

3. **Creating Issues**: Issues are created in the GitHub repository using the GitHub API.

4. **Rate Limiting**: The script includes delays between API calls to respect rate limits.

## GitHub Token Permissions

Your GitHub personal access token needs the following permissions:
- `repo` (Full control of private repositories) - Required to create issues

To create a token:
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select the `repo` scope
4. Generate and copy the token

## Limitations

- Comments on SourceForge tickets are not currently migrated
- Attachments are not migrated (SourceForge API limitations)
- The script does not close GitHub issues based on SourceForge ticket status (they are created as open)
- Rate limits apply to both SourceForge and GitHub APIs

## Troubleshooting

**"Error fetching tickets"**: Check that your SourceForge project name and tracker name are correct.

**"Error creating issue"**: Verify your GitHub token has the correct permissions and is not expired.

**Rate limiting**: If you hit rate limits, the script will log errors. Wait and retry, or use the `--limit` option to migrate fewer tickets at a time.

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
