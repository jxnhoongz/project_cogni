---
name: book-catalog-manager
description: Manages books.json catalog for 认知提升 YouTube channel. Tracks video coverage per book, prevents oversaturation (>3 uses in 30 days), suggests fresh book/angle combinations with freshness scores. Use when planning next video, checking what's been covered, updating catalog after publishing, or asking "what books haven't we covered?"
---

# Book Catalog Manager

Manages the book catalog at `/cognilab/catalog/books.json`. Tracks coverage, prevents overuse, suggests fresh content.

## Catalog Schema

```json
{
  "id": "bk_0001",
  "title": "Atomic Habits",
  "authors": ["James Clear"],
  "tags": ["habits", "behavior"],
  "status": "active",
  "coverage": {
    "shorts": [{"id": "S_2025-10-10_01", "angle": "identity-based habits", "published": "2025-10-10T12:00:00Z"}],
    "midform": []
  },
  "angle_library": ["identity vs outcome goals", "1% improvements compound", "environment design"],
  "last_used": "2025-10-10"
}
```

## Operations

### Suggest Next Book

```bash
python scripts/suggest_next_book.py --format shorts
```

Returns book with highest freshness score (days since last use / 30, max 2.0 for never-used, 0.1 penalty if >3 uses in 30 days).

### Check Oversaturation

```bash
python scripts/check_oversaturation.py --book-id bk_0001
```

Output: `{oversaturated: bool, uses_last_30d: N, max_allowed: 3}`

### Update Coverage

After publishing:

```bash
python scripts/update_coverage.py --book-id bk_0001 --video-id S_20251012_01 --angle "identity-based habits" --format shorts
```

### Get Fresh Angles

```bash
python scripts/get_fresh_angles.py --book-id bk_0001
```

Returns angles from `angle_library` not used in last 14 days.

## Edge Cases

- All books oversaturated: Flag to user, suggest adding new books
- Book ID not found: Prompt user to add to catalog
- Corrupted catalog: Restore from git

## Example Flow

User: "What book for tomorrow's short?"

1. Run `suggest_next_book.py --format shorts`
2. Get: `{book_id: "bk_0007", title: "Psychology of Money", freshness: 0.95}`
3. Run `get_fresh_angles.py --book-id bk_0007`
4. Return: "Use 'Psychology of Money' with angle 'wealth is what you don't see' (freshness: 95%)"
