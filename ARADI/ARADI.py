from numpy import zeros
# Definition of ARADI Linear Layer

A = [11, 10, 9, 8]
B = [8, 9, 4, 9]
C = [14, 11, 14, 7]


M = [zeros((32, 32)) for _ in range(4)]
for a in range(4):
    for i in range(16):
        M[a][i, i] = 1
        M[a][i, (i+A[a]) % 16] = 1
        M[a][i, 16 + (i+C[a]) % 16] = 1
        M[a][16+i, 16+i] = 1
        M[a][16+i, 16 + (i+A[a]) % 16] = 1
        M[a][16+i, (i+B[a]) % 16] = 1
