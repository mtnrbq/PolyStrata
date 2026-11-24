def parse_csv_line(line, sep=","):
    out, i, n = [], 0, len(line)
    while True:
        if i < n and line[i] == '"':
            i += 1
            buf = []
            while True:
                if i >= n:
                    raise ValueError("unterminated quote")
                if line[i] == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        buf.append('"')
                        i += 2
                        continue
                    i += 1
                    break
                buf.append(line[i])
                i += 1
            out.append("".join(buf))
            if i < n and line[i] != sep:
                raise ValueError("text after closing quote")
        else:
            j = line.find(sep, i)
            j = n if j < 0 else j
            out.append(line[i:j])
            i = j
        if i >= n:
            return out
        i += 1
        if i == n:
            out.append("")
            return out
