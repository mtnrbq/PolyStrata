def min_meeting_rooms(meetings):
    events = []
    for s, e in meetings:
        if s >= e:
            raise ValueError((s, e))
        events.append((s, 1))
        events.append((e, -1))
    events.sort()
    cur = best = 0
    for _, d in events:
        cur += d
        best = max(best, cur)
    return best
