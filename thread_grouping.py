from collections import defaultdict

def group_threads(messages):
    id_to_msg = {msg['id']: msg for msg in messages}
    child_map = defaultdict(list)
    for msg in messages:
        if msg['reply_to']:
            child_map[msg['reply_to']].append(msg['id'])

    def collect_thread(root_id):
        thread = []
        stack = [root_id]
        while stack:
            curr_id = stack.pop()
            msg = id_to_msg.get(curr_id)
            if msg:
                thread.append(msg)
                stack.extend(child_map.get(curr_id, []))
        thread.sort(key=lambda m: m['timestamp'])
        return thread

    threads = {}
    for msg in messages:
        if not msg['reply_to']:
            threads[msg['id']] = collect_thread(msg['id'])
    return threads
