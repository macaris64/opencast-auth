#!/usr/bin/env python3
"""
OpenCast Auth CLI - Simple and reliable command-line interface.
No external dependencies except requests and standard library.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import httpx


# Configuration
CONFIG_DIR = Path.home() / ".opencast"
CONFIG_FILE = CONFIG_DIR / "config.json"
TOKENS_FILE = CONFIG_DIR / "tokens.json"


class OpenCastCLI:
    """Simple CLI for OpenCast Auth API."""
    
    def __init__(self):
        """Initialize CLI."""
        self.config = self.load_config()
        self.tokens = self.load_tokens()
        self.client = httpx.Client()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not CONFIG_FILE.exists():
            return {}
        
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}")
            return {}
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        CONFIG_DIR.mkdir(exist_ok=True)
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
        except IOError as e:
            print(f"Error saving config: {e}")
            sys.exit(1)
    
    def load_tokens(self) -> Dict[str, Any]:
        """Load tokens from file."""
        if not TOKENS_FILE.exists():
            return {}
        
        try:
            with open(TOKENS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading tokens: {e}")
            return {}
    
    def save_tokens(self, tokens: Dict[str, Any]) -> None:
        """Save tokens to file."""
        CONFIG_DIR.mkdir(exist_ok=True)
        try:
            with open(TOKENS_FILE, 'w') as f:
                json.dump(tokens, f, indent=2)
        except IOError as e:
            print(f"Error saving tokens: {e}")
            sys.exit(1)
    
    def get_base_url(self) -> str:
        """Get base URL from config."""
        base_url = self.config.get('base_url', 'http://localhost:8000')
        return base_url.rstrip('/')
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with authentication if available."""
        headers = {'Content-Type': 'application/json'}
        
        access_token = self.tokens.get('access_token')
        if access_token:
            headers['Authorization'] = f'Bearer {access_token}'
        
        return headers
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request to API."""
        url = f"{self.get_base_url()}{endpoint}"
        headers = self.get_headers()
        
        try:
            if method.upper() == 'GET':
                response = self.client.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = self.client.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = self.client.put(url, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                response = self.client.delete(url, headers=headers)
            else:
                print(f"Unsupported method: {method}")
                return None
            
            if response.status_code == 401:
                print("Authentication failed. Please login again.")
                return None
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except httpx.RequestError as e:
            print(f"Request failed: {e}")
            return None
    
    def cmd_configure(self, args) -> None:
        """Configure CLI settings."""
        config = self.config.copy()
        
        if args.base_url:
            config['base_url'] = args.base_url
            print(f"Base URL set to: {args.base_url}")
        
        if args.show:
            print("Current configuration:")
            print(json.dumps(config, indent=2))
            return
        
        self.save_config(config)
        print("Configuration saved.")
    
    def cmd_login(self, args) -> None:
        """Login to get access tokens."""
        if not args.email or not args.password:
            print("Email and password are required for login.")
            sys.exit(1)
        
        data = {
            'email': args.email,
            'password': args.password
        }
        
        result = self.make_request('POST', '/api/accounts/login/', data)
        if result:
            tokens = {
                'access_token': result.get('access'),
                'refresh_token': result.get('refresh')
            }
            self.save_tokens(tokens)
            print("Login successful!")
        else:
            print("Login failed.")
            sys.exit(1)
    
    def cmd_logout(self, args) -> None:
        """Logout and clear tokens."""
        refresh_token = self.tokens.get('refresh_token')
        if refresh_token:
            data = {'refresh': refresh_token}
            self.make_request('POST', '/api/accounts/logout/', data)
        
        # Clear tokens
        self.save_tokens({})
        print("Logged out successfully.")
    
    def cmd_profile(self, args) -> None:
        """Get user profile."""
        result = self.make_request('GET', '/api/accounts/profile/')
        if result:
            print("User Profile:")
            print(json.dumps(result, indent=2))
        else:
            print("Failed to get profile. Please login first.")
    
    def cmd_organizations(self, args) -> None:
        """List organizations."""
        result = self.make_request('GET', '/api/organizations/')
        if result:
            print("Organizations:")
            for org in result.get('results', []):
                print(f"- {org['name']} (ID: {org['id']})")
        else:
            print("Failed to get organizations.")
    
    def cmd_create_org(self, args) -> None:
        """Create new organization."""
        if not args.name:
            print("Organization name is required.")
            sys.exit(1)
        
        data = {
            'name': args.name,
            'description': args.description or ''
        }
        
        result = self.make_request('POST', '/api/organizations/', data)
        if result:
            print(f"Organization '{args.name}' created successfully!")
            print(f"ID: {result['id']}")
        else:
            print("Failed to create organization.")
    
    def cmd_memberships(self, args) -> None:
        """List user memberships."""
        result = self.make_request('GET', '/api/organizations/memberships/')
        if result:
            print("Your Memberships:")
            for membership in result.get('results', []):
                org_name = membership.get('organization', {}).get('name', 'Unknown')
                role_name = membership.get('role', {}).get('name', 'Unknown')
                print(f"- {org_name}: {role_name}")
        else:
            print("Failed to get memberships.")


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="OpenCast Auth CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Configure command
    config_parser = subparsers.add_parser('configure', help='Configure CLI settings')
    config_parser.add_argument('--base-url', help='API base URL')
    config_parser.add_argument('--show', action='store_true', help='Show current configuration')
    
    # Login command
    login_parser = subparsers.add_parser('login', help='Login to get access tokens')
    login_parser.add_argument('--email', required=True, help='User email')
    login_parser.add_argument('--password', required=True, help='User password')
    
    # Logout command
    subparsers.add_parser('logout', help='Logout and clear tokens')
    
    # Profile command
    subparsers.add_parser('profile', help='Get user profile')
    
    # Organizations command
    subparsers.add_parser('organizations', help='List organizations')
    
    # Create organization command
    create_org_parser = subparsers.add_parser('create-org', help='Create new organization')
    create_org_parser.add_argument('--name', required=True, help='Organization name')
    create_org_parser.add_argument('--description', help='Organization description')
    
    # Memberships command
    subparsers.add_parser('memberships', help='List user memberships')
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = OpenCastCLI()
    
    # Route to appropriate command
    command_map = {
        'configure': cli.cmd_configure,
        'login': cli.cmd_login,
        'logout': cli.cmd_logout,
        'profile': cli.cmd_profile,
        'organizations': cli.cmd_organizations,
        'create-org': cli.cmd_create_org,
        'memberships': cli.cmd_memberships,
    }
    
    command_func = command_map.get(args.command)
    if command_func:
        command_func(args)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == '__main__':
    main() 