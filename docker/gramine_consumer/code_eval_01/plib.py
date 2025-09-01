# Output:
def get_maxKey(dict):
    max = 0
    ret = None
    for k, v in dict.items():
        if (v > max):
            max = v
            ret = str(k)
        elif (v == max):
            ret += "," + str(k)
    return ret
