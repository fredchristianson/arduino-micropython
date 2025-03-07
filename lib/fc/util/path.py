
def join_path(cls,first,*rest):
    if first is None:
        return "/"
    path = first.rstrip('/ ')
    if rest is None:
        return path
    for next in rest:
        path += "/"+next.strip('/ ')
    return path