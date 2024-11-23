import gurobipy as gp
import SIMON_Validator 
from draw_SIMON import draw
from numpy import array
from numpy.linalg import inv


def getSummaryBit(M, a, b):
    # 0+0 =0 , *+0 = 0 , *+* = *
    # Non 0,0,*
    # Non 0,_ 1
    s = M.addVar(vtype="b")
    M.addConstr(2*s <= a+b)

    M.addConstr(a+b <= 1+s)
    return s


def getSummary(M, X, Y):
    n = len(X[0])
    return [[getSummaryBit(M, X[j][i], Y[j][i]) for i in range(n)] for j in range(3)]


def AND(M, a, b, c=None):
    # 0 x 0 = 0
    # * x * = *
    # * x 0 = *
    if c is None:
        c = M.addVar(vtype="b")
    M.addConstr(a+b >= c)
    M.addConstr(2*c >= a+b)
 
    return c


def Xor(M, a, b, s=None):
    if s is None:
        s = M.addVar(vtype="b")

    M.addConstr(a +b <= 2*s)

    M.addConstr(a+b >= s)

    return s


def XorState(M, X, Y, Z=None):
    if Z is None:
        Z = [M.addVar(vtype="b") for _ in range(len(X))]
    for i in range(len(X)):
        Xor(M, X[i], Y[i], Z[i])
    return Z


def ANDState(M, X, Y, Z=None):
    if Z is None:
        Z = [M.addVar(vtype="b") for _ in range(len(X))]
    for i in range(len(X)):
        AND(M, X[i], Y[i], Z[i])
    return Z


def FeistelFunction(M, state):
    x = state[8:]+state[:8]
    y = state[1:]+state[:1]
    z = state[2:] + state[:2]

    return XorState(M, z, ANDState(M, x, y))



def FindNewZerosXor(M, a, b, c):  # c=a xor b
    NewZero = M.addVar(vtype="b")
    # b = 0 => No new Zero
    M.addConstr(b >= NewZero)
    # b= 1  and a=c=0 => New Zero
    M.addConstr(a+c + NewZero >= b)
    # b=1 and a=1 or c==1 => No NewZero
    M.addConstr(1 >= a+NewZero)
    M.addConstr(1 >= c+NewZero)

    return NewZero


def FindNewZeros(M,R, tmp, LL):
    n = len(R)
    return [FindNewZerosXor(M, R[i],tmp[i],LL[i]) for i in range(n)]


def my_callback(model, where):

    if where == gp.GRB.Callback.MIPSOL:

        model._solCount += 1
        n = len(model._summary[0][0])

        target_i = [[round(model.cbGetSolution(model._summary[0][0][i]))
                    for i in range(n)], [round(model.cbGetSolution(model._summary[0][1][i])) for i in range(n)]]
        target_o = [[round(model.cbGetSolution(model._summary[-1][0][i]))
                    for i in range(n)], [round(model.cbGetSolution(model._summary[-1][1][i])) for i in range(n)]]
        newZeros = [round(model.cbGetSolution(model._NewZeros[i]))
                    for i in range(len(model._NewZeros))]

        rD = len(model._summary)

    
        s = SIMON_Validator.is_differential_possible(
            target_i, target_o, rD-1, n)
     
        if s == gp.GRB.INFEASIBLE:
            nb_one = sum(target_i[0])+sum(target_i[1])+sum(target_o[0])+sum(target_o[1])
            print(f"Found an impossible differential provoked by {
                  round(sum(model.cbGetSolution(model._NewZeros)))} zeros. It has {nb_one} active bits")
            print("ID:", "".join([str(x) for x in target_i[0]]) + " "+"".join([str(x) for x in target_i[1]]),
                  " -/->  "+"".join([str(x) for x in target_o[0]]) + " " + "".join([str(x) for x in target_o[1]]))

          
            
            draw(model, "SIMON")

            model._valid += 1
            print(model.cbGet(gp.GRB.Callback.RUNTIME) )

        else:
            if model._solCount %50 ==0 :
                print(f"solution {model._solCount} is possible .. we exclude it")

            c = 0
            for i in range(len(target_i[0])):
                if round(target_i[0][i]) == 1:
                    c += 1-model._summary[0][0][i]
                # else:
                #     c += model._summary[0][0][i]
                if round(target_o[0][i]) == 1:
                    c += 1-model._summary[-1][0][i]
                # else:
                #     c += model._summary[-1][0][i]
                if round(target_i[1][i]) == 1:
                    c += 1-model._summary[0][1][i]
                # else:
                #     c += model._summary[0][1][i]
                if round(target_o[1][i]) == 1:
                    c += 1-model._summary[-1][1][i]
                # else:
                #     c += model._summary[-1][1][i]

            model.cbLazy(c >= 1)




def find_impossible_differential(rD, n):
    M = gp.Model()
    M.setParam("LazyConstraints", 1)

    M._is_zero_forward = []
    M._is_zero_backward = []
    M._summary = []
    M._NewZeros = []

    M._solCount = 0
    M._valid = 0

    L_init_dist_forward = [M.addVar(vtype='b') for _ in range(n)]
    L_init_dist_backward = [M.addVar(vtype='b') for _ in range(n)]

    R_init_dist_forward = [M.addVar(vtype='b') for _ in range(n)]
    R_init_dist_backward = [M.addVar(vtype='b') for _ in range(n)]

    tmp_init_dist_forward = FeistelFunction(M, L_init_dist_forward)
    tmp_init_dist_backward = FeistelFunction(M, L_init_dist_backward)

    M._is_zero_forward = [[L_init_dist_forward,
                           R_init_dist_forward, tmp_init_dist_forward]]
    M._is_zero_backward = [[L_init_dist_backward,
                            R_init_dist_backward, tmp_init_dist_backward]]

    M._summary.append(getSummary(
        M, M._is_zero_forward[0], M._is_zero_backward[0]))

    # Distinguisher
    for r in range(rD):

        newL_forward = XorState(
            M, M._is_zero_forward[-1][1], M._is_zero_forward[-1][2])
        newL_backward = [M.addVar(vtype='b') for _ in range(n)]

        XorState(M, newL_backward,
                 M._is_zero_backward[-1][2], M._is_zero_backward[-1][1])

        new_tmp_forward = FeistelFunction(M, newL_forward)
        new_tmp_backward = FeistelFunction(M, newL_backward)

        newR_forward = M._is_zero_forward[-1][0]
        newR_backward = M._is_zero_backward[-1][0]

        M._is_zero_forward.append(
            [newL_forward, newR_forward, new_tmp_forward])
        M._is_zero_backward.append(
            [newL_backward, newR_backward, new_tmp_backward])

        M._summary.append(getSummary(
            M, M._is_zero_forward[-1], M._is_zero_backward[-1]))

    for r in range(rD):
        M._NewZeros += FindNewZeros(M, M._summary[r][1], M._summary[r][2], M._summary[r+1][0])

    M.addConstr(gp.quicksum(M._NewZeros)>=1)

   
    # Mode 1 : maximize number of zeros 
    
    # M.setObjective(-gp.quicksum(M._NewZeros))

    # Mode 2 : Maximize number of active bits  (with heuristics Number of zeros >=3)
    # M.addConstr(gp.quicksum(M._NewZeros) >= 3)
    # M.setObjective(-(gp.quicksum(M._is_zero_forward[0][0]) + gp.quicksum(M._is_zero_forward[0][1]) +
    #                gp.quicksum(M._is_zero_backward[-1][0]) +  gp.quicksum(M._is_zero_backward[-1][1])))


    M.addConstr(M._summary[0][0][0] + M._summary[0][1][0]>=1)

    M.optimize(my_callback)

    print(f"============= {rD} rounds == SIMON-{2*n} ==  Explored {
          M._solCount} solutions and found {M._valid} ID in { round(M.Runtime,2)} seconds ==========")


find_impossible_differential(11, 16)

find_impossible_differential(12, 24)

find_impossible_differential(13, 32)

find_impossible_differential(16, 48)

find_impossible_differential(19, 64)

# find_impossible_differential(12, 16)
# find_impossible_differential(13, 24)
# find_impossible_differential(14, 32)
# find_impossible_differential(17, 48)
# find_impossible_differential(20, 64)
