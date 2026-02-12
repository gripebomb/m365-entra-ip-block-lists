#!/usr/bin/env python3
"""Fetch fresh IP ranges from provider APIs."""

import argparse
import ipaddress
import json
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path


# Provider configurations
PROVIDERS = {
    'aws': {
        'url': 'https://ip-ranges.amazonaws.com/ip-ranges.json',
        'parser': 'aws_json',
        'output': 'lists/providers/aws.txt',
    },
    'digitalocean': {
        'url': 'https://www.digitalocean.com/geo/google.csv',
        'parser': 'digitalocean_csv',
        'output': 'lists/providers/digitalocean.txt',
    },
    'linode': {
        'url': 'https://geoip.linode.com/',
        'parser': 'linode_text',
        'output': 'lists/providers/linode.txt',
    },
    'ovh': {
        'url': 'https://www.ovh.com/manager/dedicated/allowerlist.json',
        'parser': 'ovh_json',
        'output': 'lists/providers/ovh.txt',
    },
    'tor': {
        'url': 'https://check.torproject.org/exit-addresses',
        'parser': 'tor_exit',
        'output': 'lists/providers/tor-exit-nodes.txt',
    },
    'vultr': {
        'url': 'https://www.vultr.com/resources/faq/#downloadableIPRanges',
        'parser': 'vultr_html',
        'output': 'lists/providers/vultr.txt',
    },
}


def fetch_url(url: str) -> str:
    """Fetch content from a URL."""
    request = urllib.request.Request(
        url,
        headers={'User-Agent': 'm365-entra-ip-block-lists/1.0'}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode('utf-8')


def parse_aws_json(content: str) -> list[str]:
    """Parse AWS IP ranges JSON format."""
    data = json.loads(content)
    cidrs = []
    for prefix in data.get('prefixes', []):
        if 'ip_prefix' in prefix:
            cidrs.append(prefix['ip_prefix'])
    return cidrs


def parse_digitalocean_csv(content: str) -> list[str]:
    """Parse DigitalOcean CSV format."""
    cidrs = []
    for line in content.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # CSV format: range,country,city
        parts = line.split(',')
        if parts:
            cidr = parts[0].strip()
            if '/' in cidr:
                cidrs.append(cidr)
    return cidrs


def parse_linode_text(content: str) -> list[str]:
    """Parse Linode geofeed CSV format."""
    cidrs = []
    for line in content.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # CSV format: ip_prefix,alpha2code,region,city,postal_code
        parts = line.split(',')
        if parts:
            cidr = parts[0].strip()
            # Only include IPv4 addresses
            try:
                network = ipaddress.ip_network(cidr, strict=False)
                if network.version == 4:
                    cidrs.append(cidr)
            except ValueError:
                continue
    return cidrs


def parse_ovh_json(content: str) -> list[str]:
    """Parse OVH JSON format."""
    data = json.loads(content)
    cidrs = []

    # OVH format is a dict with region keys
    if isinstance(data, dict):
        for region, networks in data.items():
            if isinstance(networks, list):
                for net in networks:
                    if isinstance(net, str):
                        cidrs.append(net)
    elif isinstance(data, list):
        for net in data:
            if isinstance(net, str):
                cidrs.append(net)

    return cidrs


def parse_tor_exit(content: str) -> list[str]:
    """Parse Tor exit addresses format."""
    cidrs = []
    # Format: ExitNode ... \n Published ... \n LastStatus ... \n ExitAddress IP PORT
    for line in content.split('\n'):
        if line.startswith('ExitAddress '):
            parts = line.split()
            if len(parts) >= 2:
                ip = parts[1]
                # Convert IP to /32 CIDR
                cidrs.append(f"{ip}/32")
    return cidrs


def parse_vultr_html(content: str) -> list[str]:
    """Parse Vultr HTML page for CIDR ranges."""
    cidrs = []
    # Look for CIDR patterns in the HTML
    cidr_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})\b'
    matches = re.findall(cidr_pattern, content)
    for match in matches:
        try:
            ipaddress.ip_network(match, strict=False)
            cidrs.append(match)
        except ValueError:
            continue
    return list(set(cidrs))  # Remove duplicates


PARSERS = {
    'aws_json': parse_aws_json,
    'digitalocean_csv': parse_digitalocean_csv,
    'linode_text': parse_linode_text,
    'ovh_json': parse_ovh_json,
    'tor_exit': parse_tor_exit,
    'vultr_html': parse_vultr_html,
}


def fetch_provider(name: str, dry_run: bool = False) -> tuple[bool, int]:
    """Fetch and save IP ranges for a provider.

    Returns:
        Tuple of (success, cidr_count)
    """
    if name not in PROVIDERS:
        print(f"Error: Unknown provider '{name}'", file=sys.stderr)
        return False, 0

    config = PROVIDERS[name]
    url = config['url']
    parser_name = config['parser']
    output_path = Path(config['output'])

    print(f"Fetching {name} from {url}...")

    try:
        content = fetch_url(url)
        parser = PARSERS[parser_name]
        cidrs = parser(content)

        if not cidrs:
            print(f"  Warning: No CIDRs found for {name}", file=sys.stderr)
            return False, 0

        # Sort and deduplicate
        cidrs = sorted(set(cidrs))

        if dry_run:
            print(f"  Would write {len(cidrs)} CIDRs to {output_path}")
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                for cidr in cidrs:
                    f.write(f"{cidr}\n")
            print(f"  Wrote {len(cidrs)} CIDRs to {output_path}")

        return True, len(cidrs)

    except urllib.error.URLError as e:
        print(f"  Error fetching {name}: {e}", file=sys.stderr)
        return False, 0
    except json.JSONDecodeError as e:
        print(f"  Error parsing JSON for {name}: {e}", file=sys.stderr)
        return False, 0
    except Exception as e:
        print(f"  Error processing {name}: {e}", file=sys.stderr)
        return False, 0


def main():
    parser = argparse.ArgumentParser(
        description='Fetch fresh IP ranges from provider APIs'
    )
    parser.add_argument(
        'providers',
        nargs='*',
        choices=list(PROVIDERS.keys()) + ['all'],
        default=['all'],
        help='Providers to fetch (default: all)'
    )
    parser.add_argument(
        '-n', '--dry-run',
        action='store_true',
        help='Test connectivity without writing files'
    )
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='List available providers and exit'
    )

    args = parser.parse_args()

    if args.list:
        print("Available providers:")
        for name, config in sorted(PROVIDERS.items()):
            print(f"  {name}: {config['url']}")
        sys.exit(0)

    # Determine which providers to fetch
    if 'all' in args.providers:
        providers_to_fetch = list(PROVIDERS.keys())
    else:
        providers_to_fetch = args.providers

    # Fetch each provider
    success_count = 0
    total_cidrs = 0

    for name in providers_to_fetch:
        success, count = fetch_provider(name, args.dry_run)
        if success:
            success_count += 1
            total_cidrs += count

    # Summary
    print()
    print(f"Fetched {success_count}/{len(providers_to_fetch)} providers")
    print(f"Total CIDRs: {total_cidrs}")

    if args.dry_run:
        print("(Dry run - no files were modified)")

    sys.exit(0 if success_count == len(providers_to_fetch) else 1)


if __name__ == '__main__':
    main()
