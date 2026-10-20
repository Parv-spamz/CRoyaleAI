# Bounded public source follow-up

Read the publisher's repository at revision
eec3887c94faecb7e9108f5d53d24a86b6bf08d5 and the dataset README at the already
pinned ba54d0c89db86fd6e31096179a0141635fbef816 revision. Downloaded only the tree,
README and metadata/parser/cleaner source for inspection; none was executed.
Exact hashes are in `additional_source_metadata_followup.json`.

The publisher supports separately collected original battle metadata. The
expected `data/metadata/battles.jsonl` is absent from the complete repository
tree, and the legacy dataset manifest records `metadata_path=null`. The source
code does not supply the missing matching battle/deck/form records. Its replay
metadata matcher uses participants and crowns, checks reversed sides and rejects
multiple matches; it does not establish a timestamp-bound join for this archive.

No additional replay qualifies. No bulk raw download, inferred forms, new
reservation, browser challenge handling or credential access occurred. The
separate native catalog discovery provides a more productive route for the
already reserved, original-form data.
