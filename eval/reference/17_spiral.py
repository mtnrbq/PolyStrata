def spiral_order(matrix):
    if not matrix:
        return []
    w = len(matrix[0])
    if any(len(r) != w for r in matrix):
        raise ValueError("ragged")
    top, bottom, left, right, out = 0, len(matrix) - 1, 0, w - 1, []
    while top <= bottom and left <= right:
        out += [matrix[top][c] for c in range(left, right + 1)]
        out += [matrix[r][right] for r in range(top + 1, bottom + 1)]
        if top < bottom:
            out += [matrix[bottom][c] for c in range(right - 1, left - 1, -1)]
        if left < right:
            out += [matrix[r][left] for r in range(bottom - 1, top, -1)]
        top, bottom, left, right = top + 1, bottom - 1, left + 1, right - 1
    return out
