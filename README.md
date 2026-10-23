# Starburst Tail Start

Relocates your starting area toward the end of a **Starburst tail**, preserving its internal hyperlanes and attaching it to the galaxy through one exit.

**Experimental v0.1.2 · Stellaris PC 4.5.x · single-player**

[Download the installable ZIP](https://github.com/JustPixelll/StellarisSpawn/raw/refs/heads/main/dist/Starburst-Tail-Start-v0.1.2.zip)

## Install or update

1. Close Stellaris and its launcher, then extract the ZIP.
2. Press **Win + R**, enter **shell:Personal**, and open **Paradox Interactive → Stellaris → mod**.
3. Replace the old **niki_starburst_tail_start** folder and its matching **niki_starburst_tail_start.mod** file with the two items in the ZIP.
4. Enable **Starburst Tail Start (Experimental)** in your launcher playset.
5. Start a new single-player Starburst galaxy. The move happens after one day; the result appears after the following day's verification. Press **H** to centre on your capital.

## Recover an early v0.1.0 or v0.1.1 start

The optional recovery event works only in the first 30 days, after an older version recorded success. It runs once and is never triggered automatically on loading a save.

1. Keep a separate backup of the original save.
2. Install v0.1.2, then load the old save while paused.
3. Open the game's console and run **event ntt.20**.
4. Close the console and let one day pass for verification. Read the result before saving over anything.

Recovery moves the current starting neighbourhood again. It may include a few additional systems around the old exit; the same 24-system limit applies. If placement or verification fails, reload the backup. An already attempted v0.1.2 start cannot run recovery again. Existing campaigns after the first 30 days are outside its scope.

## What changed in v0.1.2

The previous selection rule could choose an outer-rim star on a short branch instead of the deep end of a long tail. This version measures shortest **hyperlane distance from the inner region**, then picks the deepest eligible outer system. An empire buffer, fewer links and radial distance only break ties.

The inspected 4.5.2 save exported radius as a fraction, such as **0.99458**, while the previous rim-placement check used **95**. The calculation now uses fractions consistently and converts them to percentages for display. The test model's incorrect 0–100 assumption has also been corrected.

Success is delayed until a next-day check confirms the home position, the exact original internal graph, and exactly one external connection from home to the chosen tail. The popup names the destination and reports its depth, the cluster size and the exit count. Hyperlane removal now iterates a stable system list.

## Selection and relocation

The script measures the connected galaxy and uses main-galaxy systems in the inner fifth of its radial span as starting points for a breadth-first search. Candidates must lie in the outer 15% of the main galaxy's measured radial extent. They must be unowned, have no owned planet, psionic aura or hostile-owned fleet, and be over 130 map units from every system being moved. A deeper candidate takes priority over a shallower one with a larger border buffer. This does not reserve an empty arm or guarantee no nearby AI empire.

Your home is placed 18–26 map units from the chosen target, inward when that target is at least 0.95 of the generated galaxy radius. Its eligible two-jump neighbourhood and small attached components travel with it, up to 24 systems total. Existing planets, ownership and internal hyperlanes are retained. Their precise geometry changes. The old region is reconnected and can gain local shortcut lanes. No new stars are created and no origin, civic or trait slot is used.

## Verification limits

**This release has not been launched in Stellaris here.** Thirteen local check groups execute the shipped scripts in a limited Python model, including graph depth, different iteration orders, 1,000-system layouts, repeat protection, recovery and injected placement/verification failures. A separate conservative replay used the submitted save's coordinates, hyperlanes, occupied systems, colonies, auras and fleet presence. It preserved connectivity and the attached story pocket in that model. The save itself is not bundled or modified.

Engine collision handling, fleets, fog of war, save/reload during pending verification and Mindwardens quest behaviour still require an in-game test. A successful topology check does not verify the origin's quest logic. Check the story pocket, fleets, auras and quest before continuing a campaign.

Nomads, Common Ground, Hegemon, Imperial Fiefdom, Payback and Broken Shackles are skipped for new starts. Oversized attached layouts may also be skipped. Partial placement and verification failures are explicit; reload a backup or regenerate that new galaxy.

Full instructions: [README-FIRST.txt](README-FIRST.txt). Checks: [VALIDATION.txt](VALIDATION.txt). References: [SOURCES.txt](SOURCES.txt).

## Development

The text files under **niki_starburst_tail_start/** are authoritative.

    python3 tests/validate_mod.py
    python3 tools/package_mod.py

Only Python's standard library is required. The tests are a script model, not an engine compatibility test. They cannot reconstruct a campaign's original coordinates from a post-relocation save.

For a bug report, include the full versioned result popup, a save, your game version, enabled mods, and relevant **logs/error.log** and **logs/game.log** lines. Search for **Starburst Tail Start**. Disabling the mod stops future automatic relocations; it does not undo saved changes.
