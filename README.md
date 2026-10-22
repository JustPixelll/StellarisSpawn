# Starburst Tail Start

A small Stellaris mod that relocates your starting area near the outer end of a **Starburst** tail on the first game day.

**Experimental v0.1.1 · targets PC 4.5.x · new single-player games only**

[**Download the installable ZIP**](https://github.com/JustPixelll/StellarisSpawn/raw/refs/heads/main/dist/Starburst-Tail-Start-v0.1.1.zip)

## Install on Windows

1. Close Stellaris and its launcher, then extract the ZIP.
2. Press **Win + R**, enter **shell:Personal**, and open **Paradox Interactive → Stellaris → mod**. Create **mod** if necessary.
3. Copy **both** **niki_starburst_tail_start.mod** and the **niki_starburst_tail_start folder** directly into **mod**.
   When updating, remove the old mod folder first and replace both items.
4. Open the launcher and add **Starburst Tail Start (Experimental)** to your playset.
5. Start a **new single-player Starburst galaxy**. Let **one game day** pass, read the result message, pause and press **H** to view your capital.

No dependencies, administrator access or installer executable are required. Use the vanilla 600-, 800- or 1000-star Starburst sizes for the first test.

## What moves

The mod moves your existing home system, its eligible two-jump starting neighbourhood, and small attached pockets. It preserves the cluster's internal hyperlanes and gives your home one short connection to an eligible outer-tail star. The old location is reconnected so the rest of the galaxy remains reachable; it can gain a few local shortcut lanes.

It does not use an origin, civic or trait slot. No new systems or economy bonuses are added.

The target comes from the outer 15% of the connected main galaxy's measured radial extent. Thin tails and a two-hop buffer from other empires are preferred. On crowded maps the buffer can be relaxed; the destination must still be unoccupied, free of owned planets, hostile-owned fleets and psionic auras, and separated from the original starter cluster. Neutral fleets are allowed. Your home is placed 18–26 map units from the target, inward at the extreme rim and outward otherwise. It aims for the **end region of a tail**, not necessarily the single farthest star. It does not reserve an entire empty arm.

## Fix in v0.1.1

The first version could incorrectly report **No Suitable Tail Found** because its fixed 75–94% radial band and fleet/border exclusions removed otherwise usable destinations. This update uses the generated map's outer extent, permits neutral visitors, and treats the two-hop border buffer as a preference.

Result titles show **v0.1.1**. If selection still fails, the popup and game log report the number of main, outer, unoccupied, clear and separated systems, plus the measured outer radius. Send those values with your report. If the title has no version, the launcher is still loading the old mod.

## Testing status

The actual scripts pass local checks in a limited Python graph model, including connectivity, internal hyperlanes, an attached origin-style pocket, repeat-run protection and failed placements. Four 1,000-system regressions cover compact maps, neutral fleets, endpoints beyond the old band and crowded borders. These are synthetic layouts with a small attached story pocket, not the user's save or the actual Mindwardens origin scripts. The exact rejecting filter in the reported game is still unknown. Primitive names were cross-checked against the 4.5.1 engine documentation.

**This has not been launched in Stellaris.** Engine placement, fleets, fog of war, psionic auras and origin quests still need an in-game check. Test a fresh, non-Ironman galaxy before starting a long campaign.

Mindwardens-style attached pockets are included by the graph logic, but **Mindwardens compatibility is unverified**. Inspect the story pocket, auras, fleets and quest before continuing.

Nomads, Common Ground, Hegemon, Imperial Fiefdom, Payback and Broken Shackles are skipped. Larger or unsuitable layouts can also be skipped. A partial placement failure is reported explicitly; discard that new galaxy and regenerate.

Full instructions and limitations: [README-FIRST.txt](README-FIRST.txt).  
Checks performed: [VALIDATION.txt](VALIDATION.txt).  
Technical references: [SOURCES.txt](SOURCES.txt).

## Development

The text files under **niki_starburst_tail_start/** are the authoritative source.

    python3 tests/validate_mod.py
    python3 tools/package_mod.py

Python's standard library is sufficient. The tests execute the mod's scripts in a small simulation; they are not a substitute for testing in the game.

For a bug report, include your game version, origin, enabled mods, result message, and relevant lines from **logs/error.log** and **logs/game.log**. Search **game.log** for **Starburst Tail Start**.

Disabling the mod stops it from affecting future starts. It does not undo system positions already stored in a save.

