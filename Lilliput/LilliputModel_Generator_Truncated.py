

from numpy.linalg import inv
from numpy import array
from gurobipy import *


pi = [13, 9, 14, 8, 10, 11, 12, 15, 4, 5, 3, 1, 2, 6, 0, 7]
pi = [pi.index(i) for i in range(16)]

# Try with only 0 and *, truncated base
N = 64//4


LinearLayer = [[0], [1], [2], [3], [4], [5], [6], [7], [7, 8], [6, 7, 9], [
    5, 7, 10], [4, 7, 11], [3, 7, 12], [2, 7, 13], [1, 7, 14], [0, 1, 2, 3, 4, 5, 6, 7, 15]]


def Xor(M, L, s=None):
    if s is None:
        s = M.addVar(vtype="b")

    if len(L) > 1:
        M.addConstr(sum(L) <= len(L) * s)
        M.addConstr(sum(L) >= s)
    else:
        M.addConstr(s == L[0])
    return s


def RoundFunction(M, state):
    new_state = [Xor(M, [state[i] for i in LinearLayer[j]]) for j in range(N)]
    return [new_state[pi[i]] for i in range(N)]


def InverseRoundFunction(M, state):
    state = [state[pi.index(i)] for i in range(N)]
    new_state = [Xor(M, [state[i] for i in LinearLayer[j]]) for j in range(N)]
    return new_state


def getSummaryBit(M, a, b):
    # 0+0 =0 , *+0 = 0 , *+* = *
    # Non 0,0,*
    # Non 0,_ 1
    s = M.addVar(vtype="b")
    M.addConstr(2 * s <= a+b)

    M.addConstr(a+b <= 1+s)
    return s


def getSummary(M, X, Y):
    return [getSummaryBit(M, X[i], Y[i]) for i in range(N)]





def NewZeroXor(M, L ) :
    z = M.addVar(vtype="b")
    M.addConstr(sum(L)>=z)
    for i in range(len(L)) :
        M.addConstr(z+sum([L[a] for a in range(len(L)) if a!=i]) >= L[i])
        for j in range(i+1,len(L)) :
            M.addConstr(L[i]+L[j]+z <=2)
    return z

def new_zeros(M, state_in, state_out) :
    state_out = [state_out[pi.index(i)] for i in range(N)]
    print([[k for k in LinearLayer[j]] for j in range(8,16)])
    return [NewZeroXor(M,[state_out[j]]+ [state_in[k] for k in LinearLayer[j]]) for j in range(8,16)]


def find_impossible_differential(rD):
    M = Model()
    M.setParam("LazyConstraints", 1)

    M._is_zero_forward = [[M.addVar(vtype='b') for _ in range(N)]]
    M._is_zero_backward = [[M.addVar(vtype='b') for _ in range(N)]]
    
   

    M._solCount = 0
    M._valid = 0

    for r in range(rD):
        M._is_zero_forward.append(RoundFunction(M, M._is_zero_forward[-1]))
        M._is_zero_backward = [InverseRoundFunction(
            M, M._is_zero_backward[0])]+M._is_zero_backward


    M._summary = [ getSummary(M, M._is_zero_forward[r], M._is_zero_backward[r]) for r in range(rD+1)]
    M._NewZeros =  []
    for r in range(rD) :
        M._NewZeros+= new_zeros(M, M._summary[r], M._summary[r+1])
    M.addConstr(sum(M._NewZeros) >=1)    

    M.optimize()
    for r in range(rD+1):
        s1="".join([str(round(x.X)) for x in M._is_zero_forward[r][::-1]])
        s2 ="".join([str(round(x.X)) for x in M._is_zero_backward[r][::-1]])
        s3="".join([str(round(x.X)) for x in M._summary[r][::-1]])

        print( s3[:8], s3[8:], [round(x.X) for x in M._NewZeros[8*r: 8*r+8]])


find_impossible_differential(7)
