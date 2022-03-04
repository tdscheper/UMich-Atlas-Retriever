import sys


def horizontal_align_print(
    s, width, mode='left', offsetChar=' ', end='\n', os=sys.stdout
    ):
    p = _print_to_file_func(os)

    if mode == 'left':
        offset = width - len(s)
        p(s, end='')
        for _ in range(offset):
            p(offsetChar, end='')
        p('', end=end)
    elif mode == 'right':
        offset = width - len(s)
        for _ in range(offset):
            p(offsetChar, end='')
        p(s, end=end)
    else: # center
        sIsEven = len(s) % 2 == 0
        widthIsEven = width % 2 == 0
        if sIsEven != widthIsEven:
            width += 1
        totalOffset = width - len(s)
        for _ in range(int(totalOffset / 2)):
            p(offsetChar, end='')
        p(s, end='')
        for _ in range(int(totalOffset / 2)):
            p(offsetChar, end='')
        p('', end=end)
    

def _print_to_file_func(file):
    def f(*objects, sep=' ', end='\n', flush=False):
        print(*objects, sep=sep, end=end, file=file, flush=flush)
    
    return f
