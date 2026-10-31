"""Bounded source diversity policy for V2 held collection."""
def source_attempt_budget(quality_preview: bool) -> int:
    return 12 if quality_preview else 8

def should_try_source(*,position:int,quality_preview:bool,eligible_count:int,
                      distinct_publishers:int,offline_snapshots:bool)->bool:
    if position<0 or eligible_count<0 or distinct_publishers<0:
        raise ValueError("invalid_collection_state")
    if position==0:
        return True
    if offline_snapshots or position>=source_attempt_budget(quality_preview):
        return False
    target_publishers=4 if quality_preview else 3
    target_articles=10 if quality_preview else 8
    return distinct_publishers<target_publishers or eligible_count<target_articles
