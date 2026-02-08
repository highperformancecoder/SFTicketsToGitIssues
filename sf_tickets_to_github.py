#!/usr/bin/env python3
"""
SourceForge Tickets to GitHub Issues Migration Script

This script automates the process of migrating tickets from SourceForge
to GitHub Issues.
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
import requests


# Image file extensions that should be embedded in the issue body
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp'}


class SourceForgeTicketsFetcher:
    """Fetches tickets from SourceForge project."""
    
    def __init__(self, project_name: str, tracker_name: str = "bugs"):
        """
        Initialize the SourceForge fetcher.
        
        Args:
            project_name: Name of the SourceForge project
            tracker_name: Name of the tracker (default: "bugs")
        """
        self.project_name = project_name
        self.tracker_name = tracker_name
        self.base_url = f"https://sourceforge.net/rest/p/{project_name}/{tracker_name}"
        self.logger = logging.getLogger(__name__)
    
    def fetch_tickets(self, status: str = "open", limit: int = 100) -> List[Dict]:
        """
        Fetch tickets from SourceForge.
        
        Args:
            status: Status of tickets to fetch (open, closed, or all)
            limit: Maximum number of tickets to fetch per request
            
        Returns:
            List of ticket dictionaries
        """
        tickets = []
        page = 0
        
        while True:
            url = f"{self.base_url}/search"
            params = {
                "limit": limit,
                "page": page
            }
            
            if status != "all":
                params["q"] = f"status:{status}"
            
            try:
                self.logger.info(f"Fetching tickets page {page}")
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                ticket_list = data.get("tickets", [])
                if not ticket_list:
                    break
                
                tickets.extend(ticket_list)
                
                # Check if there are more pages
                count = data.get("count", 0)
                if len(tickets) >= count:
                    break
                    
                page += 1
                time.sleep(1)  # Rate limiting
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error fetching tickets: {e}")
                break
        
        self.logger.info(f"Fetched {len(tickets)} tickets from SourceForge")
        return tickets
    
    def fetch_ticket_details(self, ticket_num: int) -> Optional[Dict]:
        """
        Fetch detailed information for a specific ticket.
        
        Args:
            ticket_num: Ticket number
            
        Returns:
            Ticket details dictionary or None if failed
        """
        url = f"{self.base_url}/{ticket_num}"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching ticket {ticket_num}: {e}")
            return None


class GitHubIssuesCreator:
    """Creates issues in GitHub repository."""
    
    def __init__(self, owner: str, repo: str, token: str):
        """
        Initialize the GitHub issues creator.
        
        Args:
            owner: GitHub repository owner
            repo: GitHub repository name
            token: GitHub personal access token
        """
        self.owner = owner
        self.repo = repo
        self.token = token
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.logger = logging.getLogger(__name__)
    
    def create_issue(self, title: str, body: str, labels: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Create a GitHub issue.
        
        Args:
            title: Issue title
            body: Issue body/description
            labels: List of labels to apply
            
        Returns:
            Created issue data or None if failed
        """
        url = f"{self.base_url}/issues"
        
        data = {
            "title": title,
            "body": body
        }
        
        if labels:
            data["labels"] = labels
        
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()
            issue = response.json()
            self.logger.info(f"Created issue #{issue['number']}: {title}")
            return issue
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error creating issue: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                self.logger.error(f"Response: {e.response.text}")
            return None
    
    def add_comment(self, issue_number: int, comment: str) -> bool:
        """
        Add a comment to a GitHub issue.
        
        Args:
            issue_number: Issue number
            comment: Comment text
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/issues/{issue_number}/comments"
        
        data = {"body": comment}
        
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()
            self.logger.info(f"Added comment to issue #{issue_number}")
            return True
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error adding comment to issue #{issue_number}: {e}")
            return False


class TicketMigrator:
    """Migrates tickets from SourceForge to GitHub."""
    
    def __init__(self, sf_project: str, sf_tracker: str, gh_owner: str, 
                 gh_repo: str, gh_token: str):
        """
        Initialize the ticket migrator.
        
        Args:
            sf_project: SourceForge project name
            sf_tracker: SourceForge tracker name
            gh_owner: GitHub repository owner
            gh_repo: GitHub repository name
            gh_token: GitHub personal access token
        """
        self.sf_fetcher = SourceForgeTicketsFetcher(sf_project, sf_tracker)
        self.gh_creator = GitHubIssuesCreator(gh_owner, gh_repo, gh_token)
        self.logger = logging.getLogger(__name__)
    
    def convert_ticket_to_issue(self, ticket: Dict, detailed_ticket: Optional[Dict] = None) -> Dict:
        """
        Convert a SourceForge ticket to GitHub issue format.
        
        Args:
            ticket: SourceForge ticket dictionary (basic info)
            detailed_ticket: Full ticket details including discussion and attachments
            
        Returns:
            Dictionary with GitHub issue data including comments
        """
        # Extract detailed ticket data once if available
        detailed_data = detailed_ticket.get("ticket", {}) if detailed_ticket else {}
        
        ticket_num = ticket.get("ticket_num", "")
        summary = ticket.get("summary", "No summary")
        status = ticket.get("status", "")
        created_date = ticket.get("created_date", "")
        mod_date = ticket.get("mod_date", "")
        reporter = ticket.get("reported_by", "unknown")
        
        # Get description from detailed ticket if available (it has the full text)
        # Otherwise fall back to basic ticket description
        description = detailed_data.get("description") or ticket.get("description", "")
        
        # Build issue title
        title = f"[SF#{ticket_num}] {summary}"
        
        # Build issue body
        body_parts = [
            f"**Migrated from SourceForge ticket #{ticket_num}**",
            "",
            f"**Original Reporter:** {reporter}",
            f"**Created:** {created_date}",
            f"**Last Modified:** {mod_date}",
            f"**Status:** {status}",
            "",
            "---",
            "",
            "## Description",
            "",
            description if description else "*(No description provided)*"
        ]
        
        # Add attachments section if available
        attachments = detailed_data.get("attachments", [])
        if attachments:
            body_parts.extend([
                "",
                "---",
                "",
                "## Attachments",
                ""
            ])
            for att in attachments:
                url = att.get("url", "")
                if url:
                    # Extract filename from URL since SourceForge doesn't provide filename attribute
                    # Use pathlib to handle URL path parsing
                    try:
                        # Parse the URL path to get the filename
                        url_path = Path(url.split('?')[0])  # Remove query params if any
                        filename = url_path.name if url_path.name else "attachment"
                    except Exception:
                        filename = "attachment"
                    
                    # Handle both full URLs and relative paths
                    # SourceForge might return full URLs or paths starting with /
                    if url.startswith("http://") or url.startswith("https://"):
                        full_url = url
                    elif url.startswith("/"):
                        full_url = f"https://sourceforge.net{url}"
                    else:
                        # Relative path without leading slash
                        full_url = f"https://sourceforge.net/{url}"
                    
                    # Check if this is an image file - embed it, otherwise link it
                    lower_filename = filename.lower()
                    if any(lower_filename.endswith(ext) for ext in IMAGE_EXTENSIONS):
                        # Embed image
                        body_parts.append(f"![{filename}]({full_url})")
                    else:
                        # Link to non-image file with filename as link text
                        body_parts.append(f"- [{filename}]({full_url})")
                else:
                    # No URL provided, skip this attachment
                    pass
        
        body = "\n".join(body_parts)
        
        # Determine labels - start with migration label
        labels = ["migrated-from-sourceforge"]
        
        # Add status label with sanitized status value
        if status:
            # Sanitize status for label (lowercase, replace spaces with hyphens)
            sanitized_status = status.lower().replace(" ", "-")
            labels.append(f"sf-status-{sanitized_status}")
        
        # Add SourceForge labels/tags if available (without sf-label- prefix)
        sf_labels = detailed_data.get("labels", [])
        if sf_labels:
            # Add SF labels as-is, only sanitizing them for GitHub compatibility
            for label in sf_labels:
                if label:
                    # Sanitize label (lowercase, replace spaces with hyphens)
                    sanitized_label = str(label).lower().replace(" ", "-")
                    labels.append(sanitized_label)
        
        # Extract comments from discussion thread
        comments = []
        discussion_thread = detailed_data.get("discussion_thread", {})
        posts = discussion_thread.get("posts", [])
        
        for post in posts:
            author = post.get("author", "unknown")
            timestamp = post.get("timestamp", "")
            text = post.get("text", "")
            
            if text:  # Only add non-empty comments
                comment_parts = [
                    f"**Comment by {author}** *(SourceForge)*",
                    f"**Date:** {timestamp}",
                    "",
                    text
                ]
                comments.append("\n".join(comment_parts))
        
        return {
            "title": title,
            "body": body,
            "labels": labels,
            "comments": comments
        }
    
    def migrate_tickets(self, status: str = "open", limit: Optional[int] = None, 
                       dry_run: bool = False) -> int:
        """
        Migrate tickets from SourceForge to GitHub.
        
        Args:
            status: Status of tickets to migrate (open, closed, or all)
            limit: Maximum number of tickets to migrate (None for all)
            dry_run: If True, don't actually create issues
            
        Returns:
            Number of successfully migrated tickets
        """
        self.logger.info(f"Starting migration (status={status}, limit={limit}, dry_run={dry_run})")
        
        # Fetch tickets
        tickets = self.sf_fetcher.fetch_tickets(status=status)
        
        if limit:
            tickets = tickets[:limit]
        
        self.logger.info(f"Migrating {len(tickets)} tickets")
        
        success_count = 0
        
        for i, ticket in enumerate(tickets, 1):
            ticket_num = ticket.get("ticket_num", "unknown")
            self.logger.info(f"Processing ticket {i}/{len(tickets)}: #{ticket_num}")
            
            # Fetch detailed ticket information
            detailed_ticket = None
            if ticket_num != "unknown":
                self.logger.debug(f"Fetching detailed information for ticket #{ticket_num}")
                detailed_ticket = self.sf_fetcher.fetch_ticket_details(ticket_num)
                if detailed_ticket:
                    time.sleep(1)  # Rate limiting for detail fetch
            
            # Convert ticket to issue format
            issue_data = self.convert_ticket_to_issue(ticket, detailed_ticket)
            
            if dry_run:
                self.logger.info(f"[DRY RUN] Would create issue: {issue_data['title']}")
                if issue_data.get("comments"):
                    self.logger.info(f"[DRY RUN] Would add {len(issue_data['comments'])} comments")
                success_count += 1
            else:
                # Create the issue
                issue = self.gh_creator.create_issue(
                    title=issue_data["title"],
                    body=issue_data["body"],
                    labels=issue_data["labels"]
                )
                
                if issue:
                    issue_number = issue.get("number")
                    
                    # Add comments if any
                    comments = issue_data.get("comments", [])
                    if comments and issue_number:
                        self.logger.info(f"Adding {len(comments)} comments to issue #{issue_number}")
                        for comment in comments:
                            self.gh_creator.add_comment(issue_number, comment)
                            time.sleep(1)  # Rate limiting for comments
                    
                    success_count += 1
                    # Rate limiting
                    time.sleep(2)
                else:
                    self.logger.error(f"Failed to create issue for ticket #{ticket_num}")
        
        self.logger.info(f"Migration complete: {success_count}/{len(tickets)} tickets migrated")
        return success_count


def load_config(config_file: str) -> Dict:
    """Load configuration from JSON file."""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading config file: {e}")
        sys.exit(1)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Migrate SourceForge tickets to GitHub issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate all open tickets
  %(prog)s --sf-project myproject --gh-owner myuser --gh-repo myrepo --gh-token TOKEN
  
  # Migrate with config file
  %(prog)s --config config.json
  
  # Dry run to see what would be migrated
  %(prog)s --config config.json --dry-run
  
  # Migrate only 5 tickets for testing
  %(prog)s --config config.json --limit 5
"""
    )
    
    # Configuration options
    parser.add_argument("--config", help="Path to JSON configuration file")
    
    # SourceForge options
    parser.add_argument("--sf-project", help="SourceForge project name")
    parser.add_argument("--sf-tracker", help="SourceForge tracker name (default: bugs)")
    
    # GitHub options
    parser.add_argument("--gh-owner", help="GitHub repository owner")
    parser.add_argument("--gh-repo", help="GitHub repository name")
    parser.add_argument("--gh-token", help="GitHub personal access token")
    
    # Migration options
    parser.add_argument("--status", default="open", 
                       choices=["open", "closed", "all"],
                       help="Status of tickets to migrate (default: open)")
    parser.add_argument("--limit", type=int, help="Maximum number of tickets to migrate")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Don't actually create issues, just show what would be done")
    
    # Logging options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    
    # Load configuration
    config = {}
    if args.config:
        config = load_config(args.config)
    
    # Get configuration values (command line args override config file)
    sf_project = args.sf_project or config.get("sf_project")
    sf_tracker = args.sf_tracker or config.get("sf_tracker", "bugs")
    gh_owner = args.gh_owner or config.get("gh_owner")
    gh_repo = args.gh_repo or config.get("gh_repo")
    gh_token = args.gh_token or config.get("gh_token") or os.environ.get("GITHUB_TOKEN")
    
    # Validate required parameters
    if not sf_project:
        logger.error("SourceForge project name is required (--sf-project or config file)")
        sys.exit(1)
    if not gh_owner:
        logger.error("GitHub owner is required (--gh-owner or config file)")
        sys.exit(1)
    if not gh_repo:
        logger.error("GitHub repository is required (--gh-repo or config file)")
        sys.exit(1)
    if not gh_token:
        logger.error("GitHub token is required (--gh-token, config file, or GITHUB_TOKEN env var)")
        sys.exit(1)
    
    # Create migrator and run migration
    migrator = TicketMigrator(sf_project, sf_tracker, gh_owner, gh_repo, gh_token)
    
    success_count = migrator.migrate_tickets(
        status=args.status,
        limit=args.limit,
        dry_run=args.dry_run
    )
    
    logger.info(f"Migration completed: {success_count} tickets migrated")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
