import gurobipy as gp
import skinny_Validator_ZC as skinny_v
from draw_skinny import draw, distinguisher_draw
from numpy import array
from numpy.linalg import inv
import math

gp.setParam("LogToConsole", 0)

# state = [s_0, s_1, ... s_15]
# S = [ s_O, s_1, s_2, s_3
#       s_4, s_5, s_6, s_7,
#                      s_11
#                      s_15]


def ShiftRow(state):
    return state[0:4] +\
        state[7:8] + state[4:7] +\
        state[10:12]+state[8:10] +\
        state[13:16]+state[12:13]


def Xor(M, L, s=None):
    if s is None:
        s = M.addVar(vtype="b")

    if len(L) > 1:
        M.addConstr(sum(L) <= len(L)* s)
        M.addConstr(sum(L) >= s)
    else:
        M.addConstr(s == L[0])
    return s


LinearLayer = array([[1, 0, 1, 1], [1, 0, 0, 0], [0, 1, 1, 0], [1, 0, 1, 0]])
LinearLayerInverse = inv(LinearLayer)
LinearLayerInverse = array(
    [[abs(round(LinearLayerInverse[i, j])) for j in range(4)] for i in range(4)])


def MixColumns(M, state, new_state):
    for i in range(4):
        MixColumn(M, state[i::4], new_state[i::4])


def MixColumn(M, col, new_col):
    for i in range(4):
        Xor(M, [col[j] for j in range(4) if LinearLayerInverse[ j,i] == 1], new_col[i])


def MixColumnsInverse(M, state, new_state):
    for i in range(4):
        MixColumnInverse(M, state[i::4], new_state[i::4])


def MixColumnInverse(M, col, new_col):
    for i in range(4):
        Xor(M, [col[j]
            for j in range(4) if LinearLayer[j,i] == 1], new_col[i])


def getSummaryBit(M, a, b):
    # 0+0 =0 , *+0 = 0 , *+* = *
    # Non 0,0,*
    # Non 0,_ 1
    s = M.addVar(vtype="b")
    M.addConstr(2 * s <= a+b )

    M.addConstr(a+b <= 1+s)
    return s


def getSummary(M, X, Y):
    return [getSummaryBit(M, X[i], Y[i]) for i in range(16)]


def FindNewZerosMixColumn(M, Known_zeros_before, Known_zeros_after):
    NewZero = M.addVar(vtype='b', name="MixColumn")
    L = Known_zeros_before + Known_zeros_after+[NewZero]
    with open("MC_Skinny_Transpose_short.esp", 'r') as f:
        for line in f:
            if line[0] != '.':
                c = 0
                for i in range(9):
                    if line[i] == '0':
                        c += L[i]
                    elif line[i] == '1':
                        c += 1-L[i]

                M.addConstr(c >= 1)

    return NewZero


def FindNewZeros(M, X, Y):
    return [FindNewZerosMixColumn(M, X[i::4], Y[i::4]) for i in range(4)]


def ExtendedKeyActiveNibbles(Model, key, state):
    Model.addConstrs(key[i] == Xor(
        Model, [state[i], state[i+4], state[i+12]]) for i in range(4))
    Model.addConstr(key[7] == state[8])
    Model.addConstrs(key[4+i] == state[9+i] for i in range(3))


def my_callback(model, where):

    if where == gp.GRB.Callback.MIPSOL:

        model._solCount += 1

        rD = len(model._is_zero_forward)
     
   

        target_i = [round(model.cbGetSolution(model._summary[0][0][i]))
                    for i in range(16)]
        target_o = [round(model.cbGetSolution(model._summary[-1][2][i]))
                    for i in range(16)]

   
        newZeros = [round(model.cbGetSolution(model._NewZeros[i]))
                    for i in range(len(model._NewZeros))]

        
        s = skinny_v.is_differential_possible(target_i, target_o, rD-1)

        if True : # s == gp.GRB.INFEASIBLE:
            print(f"Found an impossible differential provoked by {
                  round(sum(model.cbGetSolution(model._NewZeros)))} zeros")
            print("ID:", target_i, target_o)

            is_zero_forward = [[[round(model.cbGetSolution(model._is_zero_forward[rr][i][j]))
                                 for j in range(16)] for i in range(3)] for rr in range(rD)]
            is_zero_backward = [[[round(model.cbGetSolution(model._is_zero_backward[rr][i][j]))
                                  for j in range(16)] for i in range(3)] for rr in range(rD)]
            summary = [[[round(model.cbGetSolution(model._summary[rr][i][j]))
                         for j in range(16)] for i in range(3)] for rr in range(len(model._summary))]

           
            distinguisher_draw(is_zero_forward, is_zero_backward,  newZeros, summary, f"sol/ZC_solution_{rD-1}.tex")

         

            model._valid += 1
        else:
            print(f"solution {model._solCount} is possible .. we exclude it")

            c = 0
            for i in range(16):
                if round(target_i[i]) == 1:
                    c += 1-model._summary[0][0][i]
                if round(target_o[i]) == 1:
                    c += 1-model._summary[-1][2][i]

            model.cbLazy(c >= 1)

        print()


def Pi(TK):
    pi = [9, 15, 8, 13, 10, 14, 12, 11, 0, 1, 2, 3, 4, 5, 6, 7]
    return [TK[pi[i]] for i in range(16)]


def index(x, L):
    for i in range(len(L)):
        if L[i] is x:
            return i


def find_impossible_differential(rD):
    M = gp.Model()
    M.setParam("LazyConstraints", 1)

    # On all tracks : track[r] is the states during the r rounds
    # track[r][0] : after mixcolum
    # track[r][1] : after subcell
    # track[r][2] :  after shiftrow

    # round 0 to rB-1 : key recovery backward
    # round rB to rB+rD : ID distinguisher
    # round rB+rD+1 to end : key recovery forward

    M._is_zero_forward = []
    M._is_zero_backward = []
    M._summary = []
    M._NewZeros = []

    M._solCount = 0
    M._valid = 0

  
    # Distinguisher
    for r in range(rD+1):
        init_dist_forward = [M.addVar(vtype='b') for _ in range(16)]
        init_dist_backward = [M.addVar(vtype='b') for _ in range(16)]

        M._is_zero_forward.append(
            [init_dist_forward, init_dist_forward, ShiftRow(init_dist_forward)])
        M._is_zero_backward.append(
            [init_dist_backward, init_dist_backward, ShiftRow(init_dist_backward)])

        summary_state = getSummary(M, init_dist_forward, init_dist_backward)
        M._summary.append(
            [summary_state, summary_state, ShiftRow(summary_state)])


    for r in range(rD+1):

        if r > 0:
            MixColumns(M, M._is_zero_forward[r-1][2], M._is_zero_forward[r][0])
            MixColumnsInverse(
                M, M._is_zero_backward[r][0], M._is_zero_backward[r-1][2])

            M._NewZeros += FindNewZeros(M,
                                        M._summary[r-1][2], M._summary[r][0])
  
    M.addConstr(gp.quicksum(M._NewZeros) >= 1)

    M.setObjective(gp.quicksum(M._summary[0][0]))

    M.optimize(my_callback)

    print(f"=============  rD = {rD}   ==== Explored {
          M._solCount} solutions and found {M._valid} ID  in { round(M.Runtime,2)} seconds  ==========")




for r in range(10,15) :
    find_impossible_differential(r)