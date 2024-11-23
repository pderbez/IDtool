import gurobipy as gp
import SIMECK_Validator
from draw_SIMECK import draw



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

    # M.addConstr(a <= s)
    # M.addConstr(b <= s)
    M.addConstr(a+b <= 2*s)
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
    x = state
    y = state[5:]+state[:5]
    z = state[1:] + state[:1]

    return XorState(M, z, ANDState(M, x, y))



def FindNewZerosXor(M, a, b, c):  # c=a xor b
    NewZero = M.addVar(vtype="b")
    # b = 0 => No new Zero
    M.addConstr(b >= NewZero)
    # b= 1  and a=c=0 => New Zero
    M.addConstr(a+c + NewZero >= b)
    # b=1 and a=1 or c==1 => No NewZero
    M.addConstr(1-b+1-a+1-NewZero >= 1)
    M.addConstr(1-b+1-c+1-NewZero >= 1)

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
  

        rD = len(model._summary)
        nb_one = sum(target_i[0])+sum(target_i[1])+sum(target_o[0])+sum(target_o[1])
        
   
        s = SIMECK_Validator.is_differential_possible(
            target_i, target_o, rD-1, n)

        if s == gp.GRB.INFEASIBLE:
            
            print(f"Found an impossible differential provoked by {
                  round(sum(model.cbGetSolution(model._NewZeros)))} zeros. It has {nb_one} active bits" ,model.cbGet(gp.GRB.Callback.RUNTIME))
            print("ID:", "".join([str(x) for x in target_i[0]]) + " "+"".join([str(x) for x in target_i[1]]),
                  " -/->  "+"".join([str(x) for x in target_o[0]]) + " " + "".join([str(x) for x in target_o[1]]))

            
            draw(model, "SIMECK")

            model._valid += 1

            # model.cbLazy(gp.quicksum(model._is_zero_forward[0][0]) + gp.quicksum(model._is_zero_forward[0][1]) +
            #         gp.quicksum(model._is_zero_backward[-1][0]) +  gp.quicksum(model._is_zero_backward[-1][1]) >= nb_one+1)
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
    M.setParam("LogToConsole",0)
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
        # M._NewZeros += FindNewZeros(M, M._summary[r]
        #                             [0], M._summary[r][1], M._summary[r+1][0])
        M._NewZeros += FindNewZeros(M, M._summary[r][1], M._summary[r][2], M._summary[r+1][0])


    M.addConstr(gp.quicksum(M._NewZeros)>=1)

    # Mode 1 : maximize number of zeros 
    # M.setObjective(-gp.quicksum(M._NewZeros))

    # Mode 2 : Maximize number of active bits  (with heuristics Number of zeros >=3)
    M.addConstr(gp.quicksum(M._NewZeros) >= 3)
    M.setObjective(-(gp.quicksum(M._is_zero_forward[0][0]) + gp.quicksum(M._is_zero_forward[0][1]) +
                   gp.quicksum(M._is_zero_backward[-1][0]) +  gp.quicksum(M._is_zero_backward[-1][1])))


    M.addConstr(M._summary[0][0][0] + M._summary[0][1][0]>=1)

    M.optimize(my_callback)

    print(f"============= Explored {
          M._solCount} solutions and found {M._valid} ID in { round(M.Runtime,2)} seconds ==========")

find_impossible_differential(11, 16)

find_impossible_differential(15, 24)

find_impossible_differential(17, 32)



# find_impossible_differential(12, 16)

# find_impossible_differential(16, 24)

# find_impossible_differential(18, 32)




