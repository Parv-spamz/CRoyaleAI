# Public source check, October 5 10:35 EDT

The complete local unused exact-Icebow metadata set contains 183 groups and zero
opposing Goblin Barrel decks, before reconstruction exclusions. It has five Witch
deck encounters; three pass card/form preflight and two still contain unsupported
Void. The three reconstructable Witch encounters use the failed opening-hand
fallback. Repairing that mechanism may recover Witch material; it cannot create
missing Barrel encounters. These are source/deck counts, not opportunities or power.

Additional public dataset pages were inspected through ordinary web access:

- [raymond9326/clash-royale-battles](https://huggingface.co/datasets/raymond9326/clash-royale-battles)
  exposes battle summaries, participant/deck card names, crowns and tower fields
  in its displayed schema. That schema does not supply replay command timelines
  or original form flags. It is not a qualified reconstruction source.
- [josefbednar/alphaclash-replays](https://huggingface.co/datasets/josefbednar/alphaclash-replays)
  documents video replays with deck screenshot-derived sidecars. This does not
  establish authoritative original forms or complete native command streams.
- [chrisrca/clash-royale-tv-replays](https://huggingface.co/datasets/chrisrca/clash-royale-tv-replays)
  documents video frames, with image/card/coordinate labels in the preview. It
  does not establish a faithful command-plus-original-form dataset for this task.

These observations concern the documented schemas, not an exhaustive audit of
every file. No bulk download, execution of publisher code, guessed forms,
pixel-derived substitution, new reservation, account access or challenge bypass
occurred. Previously inspected Cochon123/Vanguard sources retain their recorded
limits. Further source acquisition needs faithful raw replay commands joined to
original battle/deck metadata, or owner-provided access to such a source.
