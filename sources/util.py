def merged_days(first, second):
    result = []
    for f, s in zip(first.lessons(), second.lessons()):
        if f:
            result.append(f)
        if s:
            result.append(s)
    return result


def merged_weeks(upper, lower):
    upper = dict(upper)
    lower = dict(lower)
    return [merged_days(up, down)
            for up, down in zip(upper.values(), lower.values())]


def locate(seq, pred, default=None):
    for item in seq:
        if pred(item):
            return item
    return default