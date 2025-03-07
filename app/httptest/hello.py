def fibonaccir(n):
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonaccir(n-1) + fibonaccir(n-2)
    