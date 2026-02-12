# m365-entra-ip-block-lists

Curated IPv4 CIDR block lists for Microsoft 365 / Microsoft Entra IP-based controls (Named Locations, Conditional Access, and related allow/block workflows).

## Repository Structure

```text
lists/
  providers/               # Canonical provider-specific lists
  chunks/                  # Split files for upload-size / entry-limit workflows
    aws/
    digitalocean/
    hetzner/
    hostinger/
    linode/
    ovh/
    protonvpn/
    tor-exit-nodes/
    vultr/
```

## File Inventory

### `lists/providers/`

- `aws.txt` (7,367 CIDRs)
- `digitalocean.txt` (1,051 CIDRs)
- `hetzner.txt` (81 CIDRs)
- `hostinger.txt` (859 CIDRs)
- `linode.txt` (5,132 CIDRs)
- `ovh.txt` (599 CIDRs)
- `protonvpn.txt` (830 CIDRs)
- `tor-exit-nodes.txt` (1,372 CIDRs)
- `vultr.txt` (434 CIDRs)

### `lists/chunks/`

- `aws/aws-part-001.txt` (2,000 CIDRs)
- `aws/aws-part-002.txt` (2,000 CIDRs)
- `aws/aws-part-003.txt` (2,000 CIDRs)
- `aws/aws-part-004.txt` (1,367 CIDRs)
- `digitalocean/digitalocean-part-001.txt` (1,051 CIDRs)
- `hetzner/hetzner-part-001.txt` (81 CIDRs)
- `hostinger/hostinger-part-001.txt` (859 CIDRs)
- `linode/linode-part-001.txt` (2,000 CIDRs)
- `linode/linode-part-002.txt` (2,000 CIDRs)
- `linode/linode-part-003.txt` (1,132 CIDRs)
- `ovh/ovh-part-001.txt` (599 CIDRs)
- `protonvpn/protonvpn-part-001.txt` (830 CIDRs)
- `tor-exit-nodes/tor-exit-nodes-part-001.txt` (1,372 CIDRs)
- `vultr/vultr-part-001.txt` (434 CIDRs)

## Formatting Standard

All list files are plain text with one CIDR per line, for example:

```text
203.0.113.0/24
198.51.100.10/32
```

## Intended Microsoft 365 / Entra Usage

- Use files in `lists/providers/` when one named location per provider is acceptable.
- Use files in `lists/chunks/` when you need to split uploads into multiple named locations due to platform limits.

## Maintenance Workflow

1. Replace or regenerate provider source files.
2. Re-split large files into `lists/chunks/<provider>/` as needed.
3. Validate with line counts (`wc -l`) before committing.
4. Commit with a date-stamped message indicating refresh source and date.

## Notes

- Chunk files may be identical to canonical files for smaller providers; they are kept for naming consistency in upload workflows.
- This repository currently contains IPv4 CIDR lists only.
