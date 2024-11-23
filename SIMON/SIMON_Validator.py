import gurobipy as gp
import copy


def getStr(x):
    if round(x.X) == 0:
        return "."
    else:
        return "*"


def Xor2(M, a, b):
    # 1+ 1 = 0
    # 1+0 = 1
    # 0+0 = 0
    c = M.addVar(vtype="b")
    M.addConstr(1-a+1-b+1-c >= 1)
    M.addConstr(a+b+(1-c) >= 1)
    M.addConstr(a+c+(1-b) >= 1)
    M.addConstr(c+b+(1-a) >= 1)
    return c


def Xor(M, L):
    x = Xor2(M, L[0], L[1])
    for y in L[2:]:
        x = Xor2(M, x, y)
    return x


def AND(M, a, b):
    # 1 * 1 = 0/1
    # 1* 0 = 0/1
    # 0*0 = 0
    x = M.addVar(vtype='b')
    M.addConstr(a+b >= x)
    return x


def printTrail(states):
    n = len(states[0][0])
    r = 1
    for current_state in states:
        print(f"Round {r+2}")

        print("".join(getStr(current_state[0][j]) for j in range(
            n))+"         "+"".join(getStr(current_state[1][j]) for j in range(n)))
        print("           " +
              "".join(getStr(current_state[2][j]) for j in range(n)))
        print()
        r += 1


def FeistelFunction(Model, state):
    x = state[8:]+state[:8]
    y = state[1:]+state[:1]
    z = state[2:] + state[:2]

    return [Xor2(Model, z[i], AND(Model, x[i], y[i])) for i in range(len(x))]


def Str(x):
    if round(x) == 1:
        return "*"
    else:
        return str(-round(x))


def is_differential_possible(input, output, n_rounds, n):
    gp.setParam("LogToConsole", 0)
    M = gp.Model()
    L = [M.addVar(vtype='b') for i in range(n)]  # var= 1 si diff #0
    R = [M.addVar(vtype='b') for i in range(n)]  # var= 1 si diff #0

    states = [[L, R, FeistelFunction(M, L)]]

    for r in range(n_rounds):
        L, R, tmp = states[-1]
        newL = [Xor2(M, R[i], tmp[i]) for i in range(n)]
        newR = L
        newtmp = FeistelFunction(M, newL)
        states.append([newL, newR, newtmp])

    M.addConstrs(states[0][0][i] ==  - input[0][i]
                 for i in range(n) if input[0][i] <= 0)
    # for i in range(n) :
    #     if input[0][i] >0 :
    #         print(f"no constaints on input {i}")
    M.addConstrs(states[0][1][i] ==  - input[1][i]
                 for i in range(n) if input[1][i] <= 0)
    M.addConstrs(states[-1][0][i] ==  - output[0][i]
                 for i in range(n) if output[0][i] <= 0)
    M.addConstrs(states[-1][1][i] == - output[1][i]
                 for i in range(n) if output[1][i] <= 0)

    M.setObjective(-gp.quicksum(states[0][0]+states[0][1]+states[-1][0]+states[-1][1]))
    
    M.optimize()


    IND_in = [j+x*n for j in range(n)
                      for x in range(2) if input[x][j] == 1]
    IND_out = [j+x*n for j in range(n)
                    for x in range(2) if output[x][j] == 1]
  

    if M.Status != gp.GRB.INFEASIBLE and M.ObjVal != - (len(IND_in)+len(IND_out)):
        id = "".join([Str(x) for x in input[0]]) + " "+"".join([Str(x) for x in input[1]])+" -/->  " + \
            "".join([Str(x) for x in output[0]]) + " " + \
            "".join([Str(x) for x in output[1]])
        
        sol = "".join([Str(-x.X) for x in states[0][0]]) + " "+"".join([Str(-x.X) for x in states[0][1]])+" -/->  " + \
            "".join([Str(-x.X) for x in states[-1][0]]) + " " + \
            "".join([Str(-x.X) for x in states[-1][1]])
        

        new_input = copy.deepcopy(input)
        new_output = copy.deepcopy(output)
        
        try :
            a = min(j for j in IND_in if round(states[0][j//n][j%n].X) ==0 )
            new_input[a//n][a%n] = -1
        except :
            b = min(j for j in IND_out if round(states[-1][j//n][j%n].X) ==0 )
            new_output[b//n][b%n] = -1

        
        
       
        s = is_differential_possible(new_input, new_output, n_rounds, n)
        if s == gp.GRB.INFEASIBLE :
            new_id =  "".join([Str(x) for x in new_input[0]]) + " "+"".join([Str(x) for x in new_input[1]])+" -/->  " + \
            "".join([Str(x) for x in new_output[0]]) + " " + \
            "".join([Str(x) for x in new_output[1]])
            print(new_id, "is infeasible", new_id.count("*"), " stars")
            return s

    return M.Status


if __name__ == "__main__":

    # # Test 1  : Hadipour 2024
    n = 32
    input = [[0]*n, [0]*n]
    input[1][10] = 1

    output = [[0]*n, [0]*n]
    output[0][1] = 1

    print(is_differential_possible(input, output, 11, n//2) == gp.GRB.INFEASIBLE)

    # Test 1  : Hadipour 2024
    n = 48
    input = [[0]*n, [0]*n]
    input[1][6] = 1

    output = [[0]*n, [0]*n]
    output[0][5] = 1

    print(is_differential_possible(input, output, 12, n//2) == gp.GRB.INFEASIBLE)
