from collections import defaultdict

def group_threads(messages):
    id_to_msg = {msg['id']: msg for msg in messages}
    child_map = defaultdict(list)
    for msg in messages:
        if msg['reply_to']:
            child_map[msg['reply_to']].append(msg['id'])

    def dfs(curr_id, thread, depth=0):
        msg = id_to_msg.get(curr_id)
        if msg:
            msg = dict(msg)  # Copy to avoid mutating input
            msg['depth'] = depth
            thread.append(msg)
            for child_id in child_map.get(curr_id, []):
                dfs(child_id, thread, depth + 1)

    threads = {}
    for msg in messages:
        if not msg['reply_to']:
            thread = []
            dfs(msg['id'], thread, depth=0)
            threads[msg['id']] = thread
    return threads
