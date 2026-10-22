STARBURST TAIL START — v0.1.1 EXPERIMENTAL
For Stellaris PC 4.5.x • New single-player Starburst games
Updated 22 October 2026

INSTALL — WINDOWS
1. Close Stellaris and its launcher.
2. Extract this ZIP.
3. Press Win+R, enter shell:Personal and press Enter.
   Open Paradox Interactive > Stellaris > mod.
   Create the mod folder if it does not exist.
   This uses your actual Documents folder, including OneDrive redirection.
4. Copy BOTH of these directly into that mod folder:
       niki_starburst_tail_start.mod
       niki_starburst_tail_start/
   The .mod file and the folder must be next to each other.
   Do not copy the outer Starburst-Tail-Start-v0.1.1 folder itself.
   Updating from 0.1.0? Remove the old niki_starburst_tail_start folder
   first, then copy the new folder and replace the .mod file.
5. Open the Paradox launcher. Under your playset, add and enable:
       Starburst Tail Start (Experimental)
   If missing, restart the launcher and check the folder nesting.
6. Start a NEW single-player game. Select the STARBURST galaxy shape.
   Use your usual empire and starting system.
7. Let ONE game day pass. Read the mod's result message, pause and press H
   to return to your capital. Verify the new start before committing to a run.

No Steam Workshop subscription or additional mod is required.
No executable, PowerShell script, administrator access or download is used.

WHAT IT DOES
- Uses the existing randomly generated Starburst galaxy.
- Finds an eligible outer star, preferring thin tails and endpoints.
- Moves your actual home system near that star, just inward at the extreme rim.
- Moves its unowned/player-owned two-jump neighbourhood and small attached
  branches with it, up to a total of 24 systems.
- Rebuilds the original internal hyperlanes of that starter cluster.
- Gives the cluster one connection to the rest of the galaxy via your home.
- Reconnects the old region locally so removing your cluster does not split
  the rest of the galaxy.
- Runs once, during the first day. No ongoing polling or modifiers.

Planets, pops, leaders, buildings, resources and origin selections are not
recreated or granted by this mod. Their existing systems are moved.
No new stars are added. The old region may gain local shortcut hyperlanes.

The target is selected from the outer 15% of the connected main galaxy's
measured radial extent. The script prefers thin tails with a two-hop buffer
from other empires, then dense tails with that buffer, then clear unowned
outer systems without the buffer. It never moves into an occupied system,
a system with an owned planet, a psionic aura or a hostile-owned fleet.
Neutral visiting fleets no longer block a target. The old starter cluster
must be more than 130 map units from the destination.

Your home is placed 18-26 map units from the target: outward normally,
inward if the target is at 95% or more of the nominal galactic radius.
It aims for the END REGION of a tail. It does not guarantee the single
farthest star on every map, and does not reserve an entire empty arm.
The rest of the starter cluster is packed within 65 units of your home,
towards the core. Its precise geometry changes; its internal lanes do not.

CHANGES IN 0.1.1
The first release could report "No Suitable Tail Found" even with usable
outer systems: it required a fixed 75-94% radius, rejected all fleets and
required a two-hop buffer. These filters are now adaptive or preferences as
described above. The result window includes the version. A failed tail scan
also shows counts for each filter and the measured maximum radius.

ORIGINS AND COMPATIBILITY
- This does not consume an origin, civic or trait slot.
- Attached pockets are detected by hyperlane connectivity. Components of
  up to 12 additional systems are included even beyond two jumps. Larger
  ordinary arms stay in place and are reconnected. A larger aura-bearing
  pocket causes the relocation to be skipped.
- This is intended to retain a Mindwardens-style attached story pocket.
  Mindwardens is NOT verified in-game: inspect the hostile pocket, auras,
  homeward routes and starting quest after relocation. Delayed scripts or
  distance-dependent mechanics may need a dedicated compatibility patch.
- Nomads, Common Ground, Hegemon, Imperial Fiefdom, Payback and Broken
  Shackles are deliberately skipped. These have linked starts or placement
  mechanics outside this mod's supported scope.
- Other special origins and galaxy-generation mods are unverified.
- Use the vanilla 600/800/1000-star Starburst shapes for initial testing.
- Other galaxy shapes, multiplayer and existing saves are left alone.
- Do not combine with another mod that relocates starting systems.
- The mod changes the gameplay checksum. Achievement eligibility has not
  been tested. Use a non-Ironman test start.

RESULT MESSAGES
Success: the script verified that every selected system reached the target
area and reconstructed the connections.
No suitable tail / unsupported layout: no map changes were made.
Placement incomplete / placement failed: discard that newly generated
galaxy and start again. Partial moves are not automatically rolled back.

VERIFICATION STATUS — PLEASE READ
The scripts have been checked locally against Stellaris 4.5.1's generated
effect/trigger documentation, with the move_system parameters cross-checked
against CWTools and a working open-source mod implementation.
The graph logic and package structure have been checked with synthetic maps.
Stellaris itself is NOT installed in the build environment.
This remains experimental and has NOT been tested in the Stellaris engine.
In particular engine placement, fleet relocation, aura recalculation,
camera/fog behaviour and origin quest compatibility require an in-game test.
See VALIDATION.txt for what was actually checked.

QUICK IN-GAME CHECK
- Your home is visibly near an outer tail after the first day.
- Homeworld economy, ruler and fleets are present.
- Expected guaranteed worlds and origin story systems remain reachable.
- There is a short exit to the tail, not a line across the whole map.
- Any origin-specific neighbouring country, aura or quest still behaves.
- Save, reload and verify the systems have not moved again.
For Mindwardens, verify the story pocket BEFORE playing past the first day.

IF IT DOES NOT WORK
For "No Suitable Tail Found (v0.1.1)", send the complete popup, including
the scan counts. If the title has no version, the old mod is still loaded.
The same counts are written to game.log. They narrow down which filter
rejected your generated map. The fix is tested on synthetic 1,000-system
maps, not your save; the original rejection cannot be diagnosed exactly
without the new counts or a save/log.

Also include your exact Stellaris version, chosen origin and
your enabled mod list, plus the relevant lines from:
  Documents/Paradox Interactive/Stellaris/logs/error.log
  Documents/Paradox Interactive/Stellaris/logs/game.log
Search game.log for "Starburst Tail Start".

REMOVE
Disable the mod in the launcher for future games.
Relocations already saved into a campaign are not undone by disabling it.
Delete the two installed items if you no longer want the mod listed.

MANUAL INSTALL ON OTHER PC PLATFORMS
Linux: ~/.local/share/Paradox Interactive/Stellaris/mod/
macOS: ~/Documents/Paradox Interactive/Stellaris/mod/
Copy the same .mod file and matching folder. These platforms were not tested.

SOURCE
All of this mod's implementation is included as readable text.
See SOURCES.txt for the documentation used.
