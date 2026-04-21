# Armory Update — Prediction Framework

## Update Cycle

~180 days between major Armory updates. Three confirmed data points:

| # | Update | Date | Gap |
|---|--------|------|-----|
| 1 | Armory Release | 2024-10-02 | — |
| 2 | Spring Forward | 2025-03-31 | 180d |
| 3 | Community Charms | 2025-10-02 | 185d |

Drop time: Pacific 4-5 PM (UTC 23:00-00:00).

## Signal Chain for Prediction

A major Armory update is preceded by a predictable sequence of signals. Each signal narrows the prediction window:

```
Signal 1: Submission campaign (Steam News)     → ~4 months before
Signal 2: Workshop Event Tags (code diff)      → ongoing, confirms theme
Signal 3: Submission deadline (X/Twitter)      → ~3 weeks before
Signal 4: limited_until added (items_game.txt) → ~3 weeks before
Signal 5: "Last chance" announcement (Steam)   → ~2 weeks before
Signal 6: Items expire                         → days before
Signal 7: Update drops                         → 80+ files changed
```

**How to use**: When analyzing an update, check which signals have fired. The more signals present, the closer the update:

- Only Signal 1-2 → months away, prep phase
- Signal 3-4 fired → weeks away, countdown started
- Signal 5-6 fired → imminent, days away
- Signal 7 → it's here

## How to Build the Evidence Chain

When making a prediction, connect multiple independent sources:

```
[Source A, date] + [Source B, date] + [Historical pattern] → Prediction + Confidence
```

Example reasoning structure (adapt to actual data, don't copy verbatim):
- Steam News announced a themed campaign on [date]
- @CounterStrike posted submission deadline [date] on X
- This update's code adds Workshop Event Tags matching that theme
- 180-day cycle from last update points to [date range]
- **But**: No new items in items_game.txt, no new localization → prep phase, not the drop itself

## Key Lookup Commands

```bash
# Find commit for a known version
gh api "repos/SteamTracking/GameTracking-CS2/commits?per_page=100" \
  --jq '[.[] | select(.commit.message | test("VERSION"))][0].sha'

# Find commit by date
gh api "repos/SteamTracking/GameTracking-CS2/commits?per_page=1&until=DATE_ISO" \
  --jq '.[0].sha'

# Compare two versions
gh api repos/SteamTracking/GameTracking-CS2/compare/$V1_SHA...$V2_SHA \
  --jq '.files | length'

# Download items_game.txt at any version
gh api "repos/SteamTracking/GameTracking-CS2/contents/game/csgo/pak01_dir/scripts/items/items_game.txt?ref=SHA" \
  -H "Accept: application/vnd.github.raw+json" > /tmp/items_VERSION.txt
```

## Confidence Calibration

| Data points | Confidence | Note |
|-------------|-----------|------|
| 180-day cycle | Medium | Only 3 data points, could shift |
| Drop time (Pacific PM) | High | Consistent across all 3 |
| Delisting lead time (~3wk) | Low | Only 1 confirmed observation |
| Campaign → Update gap (~4mo) | Low | Only 1 confirmed observation |

Update these confidence levels as more data points accumulate.

## Maintenance

When a new Armory update drops:
1. Add a row to the cycle table (date + gap from previous)
2. Note which signals fired and when — this refines the timing estimates
3. Adjust confidence levels if patterns hold or break
