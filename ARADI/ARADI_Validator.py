import copy
import gurobipy as gp
from ARADI import M


# Modelisation of the truncated based XOR
def Xor2(M, a, b, c=None):
    # 1+ 1 = 0/1
    # 1+0 = 1
    # 0+0 = 0
    if c is None:
        c = M.addVar(vtype='b')
    M.addConstr(a+b+(1-c) >= 1)
    M.addConstr(a+c+(1-b) >= 1)
    M.addConstr(c+b+(1-a) >= 1)
    return c

def XOR3(M,L,c):
    assert len(L)==3
    Xor2(M, L[0], Xor2(M, L[1],L[2]),c)    

def L(model, state, r, new_state):
    for i in range(32):
        XOR3(model, [state[j]  for j in range(32) if M[r][i, j] == 1], new_state[i])


# Printing the solution
def getStr(state):
    s = "".join('.' if round(s.X) == 0 else '1' for s in state)
    return s

def Str(x):
    if round(x) == 1:
        return "*"
    else:
        return str(-round(x))

def is_differential_possible(input, output, n_rounds, offset):
    M = gp.Model()
    M.setParam("LogToConsole", 0)
    states = [[M.addVar(vtype='b') for i in range(32)] for _ in range(n_rounds+1)]

    for r in range(n_rounds):
        L(M, states[r], (r+offset) % 4, states[r+1])
        L(M, states[r+1], (r+offset) % 4, states[r])

    IND_in = [j for j in range(32) if input[j] == 1]
    IND_out = [j for j in range(32) if output[j] == 1]

    if -1 not in input:
        input[IND_in[0]] = -1
        IND_in = IND_in[1:]

    M.addConstrs(states[0][i] == - input[i]
                 for i in range(32) if input[i] <= 0)
    M.addConstrs(states[-1][i] == - output[i]
                 for i in range(32) if output[i] <= 0)

    M.setObjective(-gp.quicksum(states[0][i] for i in IND_in) -  gp.quicksum(states[-1][i] for i in IND_out))
    id = "".join([Str(x) for x in input]) + " -/->  " + "".join([Str(x) for x in output])

    print(f"Try {id} in Validator model")
    M.optimize()
   
    if M.Status == gp.GRB.INFEASIBLE:
        print(f"{id} is infeasible ({id.count("*")} stars)")

    elif - round(M.ObjVal) != len(IND_in)+len(IND_out):

        new_input = copy.deepcopy(input)
        new_output = copy.deepcopy(output)

        try:
            a = min(j for j in IND_in if round(states[0][j].X) == 0)
            new_input[a] = -1
        except:
            b = min(j for j in IND_out if round(states[-1][j].X) == 0)
            new_output[b] = -1

        s = is_differential_possible(new_input, new_output, n_rounds)
        if s == gp.GRB.INFEASIBLE:
            new_id = "".join([Str(x) for x in new_input]) + \
                " -/->  " + "".join([Str(x) for x in new_output])
            print(f"{new_id} is infeasible ({new_id.count("*")} stars)")
            return s

    return M.Status
