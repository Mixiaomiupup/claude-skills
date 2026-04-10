---
name: cs2-update
description: Analyze CS2 game updates from the SteamTracking/GameTracking-CS2 GitHub repository. Use when user says "cs2 update", "cs2更新", "分析cs2", "cs2 diff", "游戏更新", or provides a GitHub compare/commit URL from the GameTracking-CS2 repo. Also use when user asks about CS2 patch notes, weapon skin changes, armory updates, item tracking, or delisting predictions.
---

# CS2 Update Analyzer

Analyze CS2 game updates by pulling diffs from [SteamTracking/GameTracking-CS2](https://github.com/SteamTracking/GameTracking-CS2), cross-referencing official sources (Steam News, @CounterStrike on X), and producing structured reports with evidence chains.

**Core principle**: Reports answer "so what" first, then provide evidence. Every conclusion must trace back to specific evidence sources: code diffs, official announcements, historical patterns.

## Input Modes & Resolving to SHA Range

All modes ultimately resolve to a `BASE_SHA...HEAD_SHA` range for analysis.

### 1. No argument — latest commit
```bash
HEAD_SHA=$(gh api "repos/SteamTracking/GameTracking-CS2/commits?per_page=1" --jq '.[0].sha')
BASE_SHA=$(gh api "repos/SteamTracking/GameTracking-CS2/commits/$HEAD_SHA" --jq '.parents[0].sha')
echo "$BASE_SHA...$HEAD_SHA"
```

### 2. Compare URL
Extract directly from URL: `https://github.com/.../compare/BASE_SHA...HEAD_SHA`

### 3. Single commit SHA
```bash
BASE_SHA=$(gh api "repos/SteamTracking/GameTracking-CS2/commits/COMMIT_SHA" --jq '.parents[0].sha')
# Then use BASE_SHA...COMMIT_SHA
```

### 4. Version number (e.g. `2000776`)
```bash
gh api "repos/SteamTracking/GameTracking-CS2/commits?per_page=5" --jq '.[] | select(.commit.message | test("2000776")) | .sha'
```
Then resolve to parent...commit as in mode 3.

## Step 1: Fetch Diff Data

```bash
# File count (check if >300 — GitHub truncates at 300 files)
gh api repos/SteamTracking/GameTracking-CS2/compare/$BASE_SHA...$HEAD_SHA --jq '[.files | length, .total_commits] | "\(.[0]) files, \(.[1]) commits"'

# Changed files list
gh api repos/SteamTracking/GameTracking-CS2/compare/$BASE_SHA...$HEAD_SHA --jq '.files[] | "\(.filename)\t\(.status)\t\(.additions)+\(.deletions)-"'

# Version info
gh api repos/SteamTracking/GameTracking-CS2/compare/$BASE_SHA...$HEAD_SHA --jq '.files[] | select(.filename == "game/csgo/steam.inf") | .patch'
```

**If >300 files changed**: The compare API truncates. Use `gh api repos/SteamTracking/GameTracking-CS2/commits/HEAD_SHA --jq '.files[] | .filename'` for single commits, or paginate for ranges. Note this in the report.

## Step 2: Cross-Reference Official Sources

Check official channels when the update touches items, workshop, or localization files. Skip for purely technical updates (only binaries/schemas changed).

### Steam News API (public, no auth)
```bash
curl -s "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=730&count=5&maxlength=300" | python3 -c "
import json, sys, datetime
data = json.load(sys.stdin)
for item in data['appnews']['newsitems']:
    dt = datetime.datetime.fromtimestamp(item['date']).strftime('%Y-%m-%d')
    print(f'{dt}  {item[\"title\"]}')
    print(f'  https://store.steampowered.com/news/app/730/view/{item[\"gid\"]}')
    print()
"
```

To read full text of a specific announcement:
```bash
curl -s "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=730&count=20&maxlength=0" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for item in data['appnews']['newsitems']:
    if 'KEYWORD' in item['title'].lower():
        print(item['contents'][:3000])
        break
"
```

### @CounterStrike on X (via anyweb)
```bash
anyweb --json search x "CounterStrike CS2" --limit 5
```
Then read relevant posts:
```bash
anyweb --json read "https://x.com/CounterStrike/status/TWEET_ID"
```

X posts sometimes contain deadlines NOT posted on Steam (e.g., community submission deadlines).

## Step 3: Classify Changed Files

| Category | File patterns | Priority | Conditional |
|----------|--------------|----------|-------------|
| **Items** | `items_game.txt` | Highest | Download & diff only if changed |
| **Localization** | `csgo_english.txt`, `resource/csgo_*.txt` | High | Check patch inline |
| **Convars** | `convars.txt` | Medium | Check patch inline |
| **Protobuf** | `Protobufs/*.proto` | Medium | Count + spot-check patches |
| **Workshop** | `cs2_workshop_manager_strings.txt` | Medium | Verify against history |
| **Binaries** | `*_strings.txt` (client/server) | Low | Verify new strings against history |
| **Version** | `steam.inf`, `built_from_cl.txt` | Info | Always check |
| **Assets** | `pak01_dir.txt` | Low | Only note count |

**Skip steps for unchanged categories.** If items_game.txt didn't change, skip Items Analysis entirely. If only binaries changed, skip Steam News check.

## Step 4: Analyze Each Category

### Items Analysis (items_game.txt)

Only when items_game.txt is in the changed files list. Download before/after and diff locally because API patches truncate large files.

```bash
gh api "repos/SteamTracking/GameTracking-CS2/contents/game/csgo/pak01_dir/scripts/items/items_game.txt?ref=$BASE_SHA" -H "Accept: application/vnd.github.raw+json" > /tmp/items_before.txt
gh api "repos/SteamTracking/GameTracking-CS2/contents/game/csgo/pak01_dir/scripts/items/items_game.txt?ref=$HEAD_SHA" -H "Accept: application/vnd.github.raw+json" > /tmp/items_after.txt
```

**Key extractions:**

1. **New items** — `diff /tmp/items_before.txt /tmp/items_after.txt | grep '^>' | grep '"name"'`
2. **Removed items** — `diff ... | grep '^<' | grep '"name"'` (distinguish real removals vs repositioned entries)
3. **Armory shop** — `grep -A10 'operational_point_redeemable'` for new redeemable items
4. **Delisting signals** — see below
5. **New tags** — `grep 'ui_show_new_tag'` and decode: `date -r TIMESTAMP`
6. **Loot lists** — changes to `revolving_loot_list` entries
7. **Icon changes** — count `icon_path` additions/removals (bulk = system refactor, not content)

**Item type patterns:**

| Pattern | Type |
|---------|------|
| `kc_*` | Keychain/Charm |
| `paper_*`, `glitter_*`, `holo_*`, `foil_*`, `lenticular_*` | Sticker |
| `crate_community_*` | Weapon Case |
| `set_*` | Collection |
| `selfopeningitem_*` | Self-opening collection drop |
| `Map Token *` | Map token |
| Weapon prefix (`ak_*`, `usps_*`, `m4a1s_*`, etc.) | Weapon skin/finish |

### Delisting Detection (`limited_until`)

The `limited_until` field signals upcoming removal. It applies to ALL item types — cases, collections, individual items, Limited Edition slot.

```bash
# Find items that GAINED limited_until
diff /tmp/items_before.txt /tmp/items_after.txt | grep '^>' | grep 'limited_until'
# Decode: date -r TIMESTAMP  (macOS)
```

**Delisting lifecycle:**
1. Items exist without `limited_until`
2. Valve adds `limited_until = TIMESTAMP` ~3 weeks before major update
3. Official "Last chance" on Steam News (sometimes X)
4. Items expire → removed from Armory
5. Next major update replaces with new content

When `limited_until` appears: check which items, when they expire (hints at update date), cross-reference Steam News.

### Localization (csgo_english.txt)

```bash
gh api "repos/SteamTracking/GameTracking-CS2/compare/$BASE_SHA...$HEAD_SHA" --jq '.files[] | select(.filename | test("csgo_english")) | .patch'
```

Key patterns: `CSGO_crate_*` (cases), `CSGO_set_*` (collections), `CSGO_crate_key_*` (keys), `xpshop_*` (armory text).

### Convars

```bash
gh api "repos/SteamTracking/GameTracking-CS2/compare/$BASE_SHA...$HEAD_SHA" --jq '.files[] | select(.filename | test("convars")) | .patch'
```

Focus on: default value changes, new/removed convars, flag changes (`developmentonly` → `release`).

### Protobuf

Protobufs define client-server protocol. Many changed files = major feature work. Check patches for new message types, new fields, renamed/removed fields.

### Workshop

```bash
gh api "repos/SteamTracking/GameTracking-CS2/compare/$BASE_SHA...$HEAD_SHA" --jq '.files[] | select(.filename | test("workshop_manager")) | .patch'
```

Look for `#CSGO_Workshop_Event_*` (themed submission categories) and `#CSGO_Workshop_Mode_*` (game modes). A campaign typically defines multiple theme tags — grep for all `Event_` entries. Their readable names also appear in `*_strings.txt`.

## Step 5: False Positive Detection

Before reporting anything as "new" in `*_strings.txt` or workshop files, verify it didn't exist in a recent previous version. SteamTracking extracts strings from game binaries via a dump tool — infrastructure changes can cause strings to vanish and reappear without actual game changes.

**How to verify against a specific historical version:**
```bash
# Find commit for a known version (e.g. Community Charms = 2000646)
HIST_SHA=$(gh api "repos/SteamTracking/GameTracking-CS2/commits?per_page=100" \
  --jq '[.[] | select(.commit.message | test("2000646"))][0].sha')

# Or find by date range (e.g. around Oct 2025)
HIST_SHA=$(gh api "repos/SteamTracking/GameTracking-CS2/commits?per_page=1&until=2025-10-03T00:00:00Z" \
  --jq '.[0].sha')

# Then check if string existed at that version
gh api "repos/SteamTracking/GameTracking-CS2/contents/PATH?ref=$HIST_SHA" \
  -H "Accept: application/vnd.github.raw+json" | grep -c "SEARCH_TERM"
```

**Quick check against recent commits** (for `*_strings.txt` dump artifacts):
```bash
OLDER_SHA=$(gh api "repos/SteamTracking/GameTracking-CS2/commits?per_page=10" --jq '.[-1].sha')
gh api "repos/SteamTracking/GameTracking-CS2/contents/PATH?ref=$OLDER_SHA" \
  -H "Accept: application/vnd.github.raw+json" | grep -c "SEARCH_TERM"
```

For `items_game.txt` and `csgo_english.txt`, false positives are rare — these are data files, not binary dumps. Focus verification on `*_strings.txt` files.

**Cross-version comparison** (e.g. "what changed between Spring Forward and Community Charms"):
```bash
# Resolve two version SHAs, then use the standard compare flow
gh api repos/SteamTracking/GameTracking-CS2/compare/$V1_SHA...$V2_SHA --jq '.files | length'
```
This is useful for tracking Armory content rotation — what got added/removed between major updates.

**If a string existed before but temporarily disappeared**: Report it as "reappeared (dump tool artifact)" rather than "new". Note this transparently in the report.

## Step 6: Pattern Recognition

Combine code evidence with official sources to classify the update:

| Type | Key signals |
|------|------------|
| **Armory update** | New items in items_game.txt + new loot lists + new localization + 80+ files |
| **Armory prep** | Workshop event tags + no new items_game content + within 180-day window |
| **Delisting** | `limited_until` added to existing items + Steam "Last chance" post |
| **Gameplay patch** | Convar/protobuf changes + no item changes |
| **Technical** | Only binary strings / schemas / assets |

**Armory signals checklist:**

- [ ] `items_game.txt` has new items + `operational_point_redeemable`?
- [ ] `limited_until` added to existing items?
- [ ] `csgo_english.txt` has `CSGO_crate_*` / `CSGO_set_*`?
- [ ] Workshop event tags present?
- [ ] ~180 days since last Armory update?
- [ ] Steam News "Last chance" or campaign announcement?

## Step 7: Output Report

Lead with conclusions, then evidence.

```markdown
## CS2 Update Analysis — Version XXXX (YYYY-MM-DD)

**Version**: XXXX → YYYY | **Source Revision**: AAAA → BBBB
**Commits**: N | **Files changed**: N
**Update type**: [Armory Update / Armory Prep / Delisting / Gameplay Patch / Technical]

### Key Takeaways

Each takeaway: conclusion first, then the evidence chain that supports it.

- **[Conclusion]**
  - Evidence: [source A, date] + [source B, date] → [reasoning]
  - Caveat: [what's missing or uncertain]

### [Category sections — only include categories with changes]
...

### Armory Timeline Context

| Update | Date | Gap | Key content |
|--------|------|-----|-------------|
| [historical entries] | ... | ... | ... |
| **This update** | YYYY-MM-DD | Nd | [summary] |
| **Predicted next** | ~YYYY-MM-DD | ~180d | [based on pattern] |
```

## Historical Reference

Quick summary (detailed history with commits, delisting events, campaigns → read `references/armory-history.md`):

| Update | Date | Version | Gap | Key content |
|--------|------|---------|-----|-------------|
| Armory Release | 2024-10-02 | 2000404 | — | Entire armory system |
| Spring Forward | 2025-03-31 | 2000509 | 180d | Fever Case, 3 timed drop collections |
| Community Charms | 2025-10-02 | 2000646 | 185d | 87 new charms/stickers |

**Pattern**: ~180 days (April + October). Drop time: Pacific 4-5 PM (UTC 23:00-00:00).

**Armory Prep Pipeline**: Campaign (~4mo before) → Event Tags → Deadline (~3wk) → `limited_until` added → "Last chance" → Items expire → Update drops

## Notes

- `items_game.txt` is 200k+ lines. Download and diff locally — API patches get truncated.
- `*_strings.txt` files are binary dumps — mostly memory address shifts. Only flag genuinely new readable strings after historical verification.
- `weapon_` prefix in removals may be deprecated game mode weapons (Danger Zone), not player skins.
- `limited_until` applies to ALL item types, not just the Limited Edition slot.
- macOS `grep` lacks `-P`. Use `grep -E` or `awk`.
- GitHub Compare API truncates at 300 files. Note this in reports for large updates.
