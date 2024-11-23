import gurobipy as gp
import skinny_Validator as skinny_v
from draw_skinny import draw
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
        Xor(M, [col[j] for j in range(4) if LinearLayer[i, j] == 1], new_col[i])


def MixColumnsInverse(M, state, new_state):
    for i in range(4):
        MixColumnInverse(M, state[i::4], new_state[i::4])


def MixColumnInverse(M, col, new_col):
    for i in range(4):
        Xor(M, [col[j]
            for j in range(4) if LinearLayerInverse[i, j] == 1], new_col[i])


def MixColumnsGuess(M, state, new_state):
    for i in range(4):
        MixColumnGuess(M, state[i::4], new_state[i::4])


def MixColumnGuess(M, col, new_col):
    for i in range(4):
        Xor(M, [col[j] for j in range(4) if LinearLayer[j, i] == 1], new_col[i])


def MixColumnsInverseGuess(M, state, new_state):
    for i in range(4):
        MixColumnInverseGuess(M, state[i::4], new_state[i::4])


def MixColumnInverseGuess(M, col, new_col):
    for i in range(4):
        Xor(M, [col[j]
            for j in range(4) if LinearLayerInverse[j, i] == 1], new_col[i])


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
    with open("MC_SKINNY_short.esp", 'r') as f:
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
        rB = len(model._TruncB_value_needed)
        rF = len(model._TruncF_value_needed)
        r = len(model._summary)

        target_i = [round(model.cbGetSolution(model._summary[rB][0][i]))
                    for i in range(16)]
        target_o = [round(model.cbGetSolution(model._summary[rB+rD-1][2][i]))
                    for i in range(16)]

        STKey = [[round(model.cbGetSolution(model._STKey[rr][i]))
                  for i in range(8)] for rr in range(len(model._STKey))]

        # for rr in range(len(STKey)):
        #     print(f"ST_{rr} : ", STKey[rr], model._KeySchedule[rr])

        Count_key = [round(model.cbGetSolution(
            model._Count_Key_Value[i])) for i in range(16)]
        Bounded_Count_key = [round(model.cbGetSolution(
            model._Bounded_Count_Key_Value[i])) for i in range(16)]

        complexity = round(model.cbGetSolution(model._complexity), 2)

        newZeros = [round(model.cbGetSolution(model._NewZeros[i]))
                    for i in range(len(model._NewZeros))]

        
        s = skinny_v.is_differential_possible(target_i, target_o, rD-1)

        if s == gp.GRB.INFEASIBLE:
            print(f"Found an impossible differential provoked by {
                  round(sum(model.cbGetSolution(model._NewZeros)))} zeros")
            print("ID:", target_i, target_o)

            is_zero_forward = [[[round(model.cbGetSolution(model._is_zero_forward[rr][i][j]))
                                 for j in range(16)] for i in range(3)] for rr in range(rD)]
            is_zero_backward = [[[round(model.cbGetSolution(model._is_zero_backward[rr][i][j]))
                                  for j in range(16)] for i in range(3)] for rr in range(rD)]
            summary = [[[round(model.cbGetSolution(model._summary[rr][i][j]))
                         for j in range(16)] for i in range(3)] for rr in range(len(model._summary))]

            TruncB_value_needed = [[[round(model.cbGetSolution(model._TruncB_value_needed[rr][i][j]))
                                     for j in range(16)] for i in range(3)] for rr in range(rB)]
            TruncF_value_needed = [[[round(model.cbGetSolution(model._TruncF_value_needed[rr][i][j]))
                                     for j in range(16)] for i in range(3)] for rr in range(rF)]

            draw(is_zero_forward, is_zero_backward,  newZeros, summary, TruncB_value_needed, TruncF_value_needed, STKey, Bounded_Count_key, model._KeySchedule,
                 f"sol/new_solution_{r-1}rounds_{rB}_{rD-1}_{rF}_{complexity}_{str(sum(Bounded_Count_key))}.tex")

            print("Key counts : " + str(Count_key) + " \t  Bounded Key counts :  "+str(Bounded_Count_key) +
                  "\t  Total key cells : "+str(sum(Bounded_Count_key)))
            print(f"Complexity = {complexity}")

            model._valid += 1
        else:
            print(f"solution {model._solCount} is possible .. we exclude it")

            c = 0
            for i in range(16):
                if round(target_i[i]) == 1:
                    c += 1-model._summary[rB][0][i]
                if round(target_o[i]) == 1:
                    c += 1-model._summary[rB+rD-1][2][i]

            model.cbLazy(c >= 1)

        print()


def Pi(TK):
    pi = [9, 15, 8, 13, 10, 14, 12, 11, 0, 1, 2, 3, 4, 5, 6, 7]
    return [TK[pi[i]] for i in range(16)]


def index(x, L):
    for i in range(len(L)):
        if L[i] is x:
            return i


def find_impossible_differential(rB, rD, rF, TweakSize, best_attack=1000, c=8):
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

    M._TruncB_value_needed = []
    M._TruncF_value_needed = []

    M._solCount = 0
    M._valid = 0

    M._STKey = [[M.addVar(vtype='b', name=f"SK_{r}_{i}") for i in range(
        8)] for r in range(rB+rD+rF+1)]

    M._KeySchedule = [[i for i in range(16)]]

    for r in range(rB+rD+rF):
        M._KeySchedule.append(Pi(M._KeySchedule[-1]))

    for r in range(rB):
        init = [M.addVar(vtype='b') for _ in range(16)]

        init_value_needed = [M.addVar(vtype='b') for _ in range(16)]
        value_needed_after_subcells = [M.addVar(vtype='b') for _ in range(16)]

        M._summary.append([init, init, ShiftRow(init)])
        M._TruncB_value_needed.append(
            [init_value_needed, value_needed_after_subcells, ShiftRow(value_needed_after_subcells)])

    for r in range(0, rB):
        if r > 0:
            MixColumnsInverse(M, M._summary[r][0], M._summary[r-1][2])
            MixColumnsGuess(
                M, M._TruncB_value_needed[r][0], M._TruncB_value_needed[r-1][2])
            ExtendedKeyActiveNibbles(
                M, M._STKey[r-1], M._TruncB_value_needed[r][0])

        for i in range(16):
            Xor(M, [M._summary[r][1][i], M._TruncB_value_needed[r]
                [1][i]], M._TruncB_value_needed[r][0][i])

    M.addConstrs(M._STKey[rB-1][i] == 0 for i in range(8))
    M.addConstrs(M._TruncB_value_needed[rB-1][2][i] == 0 for i in range(16))

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

    MixColumnsInverse(M, M._summary[rB][0], M._summary[rB-1][2])

    for r in range(rD+1):

        if r > 0:
            MixColumns(M, M._is_zero_forward[r-1][2], M._is_zero_forward[r][0])
            MixColumnsInverse(
                M, M._is_zero_backward[r][0], M._is_zero_backward[r-1][2])

            M._NewZeros += FindNewZeros(M,
                                        M._summary[rB+r-1][2], M._summary[rB+r][0])
        M.addConstrs(M._STKey[rB+r][i] == 0 for i in range(8))

    # Key Recovery forward

    for r in range(rF):

        init = [M.addVar(vtype='b') for _ in range(16)]
        M._summary.append([init, init, ShiftRow(init)])

        init_value_needed = [M.addVar(vtype='b') for _ in range(16)]
        value_needed_after_subcells = [M.addVar(vtype='b') for _ in range(16)]

        M._TruncF_value_needed.append(
            [init_value_needed, value_needed_after_subcells, ShiftRow(value_needed_after_subcells)])

    for r in range(rF):

        MixColumns(M, M._summary[rB+rD+r][2], M._summary[rB+rD+r+1][0])
        if r > 0:
            MixColumnsInverseGuess(
                M, M._TruncF_value_needed[r-1][2], M._TruncF_value_needed[r][0])
        else:
            M.addConstrs(
                M._TruncF_value_needed[0][0][i] == 0 for i in range(16))
        for i in range(16):
            Xor(M, [M._TruncF_value_needed[r][0][i], M._summary[rB +
                rD+r+1][1][i]], M._TruncF_value_needed[r][1][i])

        M.addConstrs(M._STKey[rB+rD+1+r][i] ==
                     M._TruncF_value_needed[r][1][i] for i in range(8))

    # formula = max(cin+cout - 0.5 , |kin u kout| - 0.5, cin + cout - 0.5 +  n + 1 - |Din| - |Dout|, (cin + cout - 0.5 + n + 1 - |Din|)/2)
    Din = c * gp.quicksum(M._summary[1][0])  # first round is "free"
    Dout = c*gp.quicksum(M._summary[-2][0])  # last round is "free"
    DX = c*gp.quicksum(M._summary[rB][0])
    DY = c*gp.quicksum(M._summary[rB+rD][-1])
    cin = Din-DX
    cout = Dout-DY

    Count_Key_Expr = [gp.quicksum(M._STKey[r][i] for r in range(rB+rD+rF)
                                  for i in range(8) if M._KeySchedule[r][i] == j) for j in range(16)]

    M._Count_Key_Value = [M.addVar(vtype='int', lb=0) for _ in range(16)]
    M.addConstrs(M._Count_Key_Value[i] == Count_Key_Expr[i] for i in range(16))

    M._Bounded_Count_Key_Value = [
        M.addVar(vtype='int', lb=0) for _ in range(16)]
    M.addConstrs(M._Bounded_Count_Key_Value[i] == gp.min_(
        M._Count_Key_Value[i], constant=TweakSize) for i in range(16))

    KinKout = c * gp.quicksum(M._Bounded_Count_Key_Value)
    n = c*16

    # formula = max(cin+cout - 0.5 , |kin u kout| - 0.5, cin + cout - 0.5 +  n + 1 - |Din| - |Dout|, (cin + cout - 0.5 + n + 1 - |Din|)/2)
    Term1, Term2, Term3, Term4, complexity = [
        M.addVar(vtype=gp.GRB.CONTINUOUS) for _ in range(5)]
    M.addConstr(Term1 == cin+cout - 0.53)
    M.addConstr(Term2 == KinKout - 0.53)
    M.addConstr(Term3 == cin+cout - 0.53+n+1 - Din-Dout)
    M.addConstr(Term4 == (cin+cout-0.53+n+1-Dout)/2)

    # M.addGenConstrMax(complexity, [Term1, Term2, Term3, Term4])
    M.addConstr(complexity >= Term1)
    M.addConstr(complexity >= Term2)
    M.addConstr(complexity >= Term3)
    M.addConstr(complexity >= Term4)

    M._complexity = complexity

    M.setObjective(complexity)
    M.setObjectiveN(-gp.quicksum(M._Bounded_Count_Key_Value),1)

    M.addConstr(complexity <= best_attack)
    M.addConstr(gp.quicksum(M._NewZeros) >= 1)

    M.optimize(my_callback)

    try:
        obj = round(M.ObjVal)
        D = max(Term3.X, Term4.X)
        T = max(Term1.X, Term2.X)
        lower_bound_complexity = min(math.log2(2**(D)*g + 2**(T)*g*(rB+rF-2)/(
            rB+rD+rF) + 2**(16*c*TweakSize - g)) for g in range(1, 50))
        # print([(g,math.log2(2**(T)*g*(rB+rF-2)/(
        #     rB+rD+rF) + 2**(16*c*TweakSize - g))) for g in range(10, 40)])

    except:
        obj = 1000

    print(f"Complexity= {complexity.X}")
    print(f"cin = {cin.getValue()//c}, cout = {cout.getValue()//c}")
    print(f"Din = {Din.getValue()//c}, DX= {DX.getValue()//c}, DY = {
          DY.getValue()//c}, Dout= {Dout.getValue()//c}")
    print(f"Term1= {Term1.X}, Term2 = {
          Term2.X}, Term3= {Term3.X}, Term4 = {Term4.X}")
    print(f"============= rB = {rB} rD = {rD} rF = {rF}  ==== Explored {
          M._solCount} solutions and found {M._valid} ID  in { round(M.Runtime,2)} seconds. Lower bound complexity = 2^{lower_bound_complexity}  ==========")
    return obj





find_impossible_differential(3, 11, 3, 1, c=4)
find_impossible_differential(3, 11, 3, 1, c=8)

find_impossible_differential(3, 11, 5, 2, c=4)
find_impossible_differential(3, 11, 5, 2, c=8)

find_impossible_differential(5, 11, 5, 3, c=4)
find_impossible_differential(5, 11, 5, 3, c=8)
