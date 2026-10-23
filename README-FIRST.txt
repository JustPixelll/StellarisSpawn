STARBURST TAIL START — v0.1.2 EXPERIMENTAL
For Stellaris PC 4.5.x • New single-player Starburst games
Updated 23 October 2026

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
   Do not copy the outer Starburst-Tail-Start-v0.1.2 folder itself.
   Updating from an older version? Remove the old niki_starburst_tail_start folder
   first, then copy the new folder and replace the .mod file.
5. Open the Paradox launcher. Under your playset, add and enable:
       Starburst Tail Start (Experimental)
   If missing, restart the launcher and check the folder nesting.
6. Start a NEW single-player game. Select the STARBURST galaxy shape.
   Use your usual empire and starting system.
7. Let TWO game days pass: one for the move, one for verification. Read
   the result message, pause and press H to return to your capital.

No Steam Workshop subscription or additional mod is required.
No executable, PowerShell script, administrator access or download is used.

WHAT IT DOES
- Uses the existing randomly generated Starburst galaxy.
- Finds the deepest eligible outer system by hyperlane distance from the
  inner region, then breaks ties using border buffer, degree and radius.
- Moves your actual home system near that star, just inward at the extreme rim.
- Moves its unowned/player-owned two-jump neighbourhood and small attached
  branches with it, up to a total of 24 systems.
- Rebuilds the original internal hyperlanes of that starter cluster.
- Gives the cluster one connection to the rest of the galaxy via your home.
- Reconnects the old region locally so removing your cluster does not split
  the rest of the galaxy.
- Moves once, then verifies on the following day. No ongoing polling.

Planets, pops, leaders, buildings, resources and origin selections are not
recreated or granted by this mod. Their existing systems are moved.
No new stars are added. The old region may gain local shortcut hyperlanes.

The script measures distance ALONG HYPERLANES from the inner region, using
all main systems in the inner fifth of the measured radial span as seeds.
The target must be in the outer 15% of the main galaxy's radial extent.
The deepest eligible target wins. A two-hop border buffer, fewer links and
radius only break ties, so a shorter outer branch cannot outrank a long tail.
The target remains unowned, without owned planets, auras or hostile-owned
fleets, and over 130 map units from the original starter cluster.

The home is placed 18-26 units from the target: inward if its radius fraction
is at least 0.95, otherwise outward. Companion systems are requested within
65 units of home; placement checks allow up to 80. Internal lanes are kept,
but precise geometry changes. This does not reserve an empty arm or exclude
nearby AI empires. The deepest available target may be near another empire.

FIX IN 0.1.2
- Replaces radial ranking with hyperlane depth so a short outer branch does
  not win merely because it reaches a slightly larger radius.
- Corrects a radius-unit error confirmed by the supplied 4.5.2 save: the
  engine exported 0.99458, not 99.458. Calculations now use fractions.
- Delays success until the next day, checking position, original internal
  lanes and exactly one external exit from home to the chosen target.
- Names the selected target and shows depth and verification counts.
- Adds optional one-time recovery for early starts moved by an old version.

RECOVER THE EXISTING EARLY SAVE
1. Keep a separate backup of your .sav file.
2. Update the mod, launch Stellaris and load the old save while paused.
3. Open the game's console and enter:
       event ntt.20
4. Close the console and let ONE day pass. Read the versioned result.

This recovery command is only for an older version's successful attempt,
before 30 days have passed. It cannot repeat after a v0.1.2 attempt and does
not run automatically on loading. The current neighbourhood may include a
few additional stars near the previous exit. The 24-system cap still applies.
On a failure, reload your backup; partial moves are not rolled back.

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
- Other galaxy shapes and multiplayer are left alone. Existing saves only
  change if you explicitly run the early recovery command above.
- Do not combine with another mod that relocates starting systems.
- The mod changes the gameplay checksum. Achievement eligibility has not
  been tested. Use a non-Ironman test start.

RESULT MESSAGES
Success: the next-day check verified the home position, all selected
systems within range, the original internal lanes and exactly one exit.
No suitable tail / unsupported layout: no map changes were made.
Placement incomplete / placement failed / verification failed: reload
your backup or discard that newly generated galaxy and start again. Partial moves are not automatically rolled back.

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
- Your home is near the selected tail after the versioned success message.
- Homeworld economy, ruler and fleets are present.
- Expected guaranteed worlds and origin story systems remain reachable.
- There is a short exit to the tail, not a line across the whole map.
- Any origin-specific neighbouring country, aura or quest still behaves.
- Save, reload and verify the systems have not moved again.
For Mindwardens, verify the story pocket immediately after confirmation.

IF IT DOES NOT WORK
For "No Suitable Tail Found (v0.1.2)", send the complete popup, including
the scan counts. If the title has no version, the old mod is still loaded.
The same counts are written to game.log. They narrow down which filter
rejected your generated map. The scripts were checked in a model with
synthetic maps and geometry from the submitted save. No engine run has
been performed here; include your new save and logs for further diagnosis.

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
