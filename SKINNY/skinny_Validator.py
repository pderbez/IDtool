import gurobipy as gp


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


def Xor2(M, a, b):
    # 1+ 1 = 0/1
    # 1+0 = 1
    # 0+0 = 0
    c = M.addVar(vtype="b")
    M.addConstr(a+b+(1-c) >= 1)
    M.addConstr(a+c+(1-b) >= 1)
    M.addConstr(c+b+(1-a) >= 1)
    return c


def Xor(M, L):
    x = Xor2(M, L[0], L[1])
    for y in L[2:]:
        x = Xor2(M, x, y)
    return x


def MixColumn(M, col):
    new_col = [Xor(M, [col[0], col[2], col[3]]), col[0], Xor(
        M, [col[1], col[2]]), Xor(M, [col[0], col[2]])]
    M.addConstr(col[1] == Xor(M, new_col[1:]))
    M.addConstr(col[2] == Xor(M, [new_col[1], new_col[3]]))
    M.addConstr(col[3] == Xor(M, [new_col[0], new_col[3]]))
    return new_col


def MixColumns(M, state):
    cols = [state[i::4] for i in range(4)]
    new_cols = [MixColumn(M, col) for col in cols]
    return [new_cols[i % 4][i//4] for i in range(16)]


def getStr(x):
    if round(x.X) == 0:
        return "-"
    else:
        return "X"


def printTrail(states):
    r=1
    for current_state in states:
        print(f"Round {r}")
        for i in range(4):
            s = "".join(getStr(current_state[0][j]) for j in range(
                4*i, 4*i+4)) + "   "+"".join(getStr(current_state[1][j]) for j in range(4*i, 4*i+4))
            print(s)
        print()
        r+=1


def is_differential_possible(input, output, n_rounds):
    gp.setParam("LogToConsole", 0)
    M = gp.Model()
    state = [M.addVar(vtype='b') for i in range(16)]  # var= 1 si diff #0
    states = [[state, ShiftRow(state)]]
    state = states[-1][-1]
    for r in range(n_rounds):
        state = MixColumns(M, state)
        states.append([state, ShiftRow(state)])
        state = states[-1][-1]

    M.addConstrs(states[0][0][i] == input[i] for i in range(16))
    M.addConstrs(states[-1][1][i] == output[i] for i in range(16))
    M.optimize()
    # if M.Status !=gp.GRB.INFEASIBLE :
    #     printTrail(states)
   
    return M.Status


if __name__ =="__main__" :
    # Test 1 : Tout à zero
    input = [0 for i in range(16)]
    output = [0 for i in range(16)]
    print(is_differential_possible(input, output, 10) == gp.GRB.OPTIMAL)

    # Test 2 : Tout à 1
    input = [1 for i in range(16)]
    output = [1 for i in range(16)]
    print(is_differential_possible(input, output, 10) == gp.GRB.OPTIMAL)

    # Test 3 : Actif en entrée, inactif en sortie
    input = [0 for i in range(16)]
    output = [1 for i in range(16)]
    print(is_differential_possible(input, output, 10) == gp.GRB.INFEASIBLE)

    # Test 4 : ID en 11 tours de Skinny (papier original)
    input = [0 for i in range(16)]
    output = [0 for i in range(16)]
    input[12]=1
    output[10]=1
    print(is_differential_possible(input,output,11)==gp.GRB.INFEASIBLE)

    # Test 4 : ID en 11 tours de Skinny (Hossein 2022)
    input = [0 for i in range(16)]
    output = [0 for i in range(16)]
    input[15]=1
    output[9]=1
    print(is_differential_possible(input,output,11)==gp.GRB.INFEASIBLE)

    

