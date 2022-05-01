# Sync2DavCal

Script that synchronizes various providers with CalDav.

## Installation

- Clone this repository.
- Run `pip install -r requirements.txt` to install dependencies
- Run `main.py`

## Configuration

Overwrite settings from `config.default.yml` by creating a file `config.yml`.

## Providers

### GitHub Notifications

Syncs (GitHub notifications)[https://github.com/notifications].
Limitation: Currently the GitHub API does not allow marking notifications as `unread`.
