
def join_path(first,*rest):
    if first is None:
        first = ""
    path = first.rstrip('/')
    if rest is None:
        return path
    for next in rest:
        path += "/"+next.strip('/')
    return path