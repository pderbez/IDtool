import gurobipy as gp



def Xor2(M, a, b):
    # 1+ 1 = 0
    # 1+0 = 1
    # 0+0 = 0
    c = M.addVar(vtype="b")
    M.addConstr(1-a+1-b+1-c>=1)
    M.addConstr(a+b+(1-c) >= 1)
    M.addConstr(a+c+(1-b) >= 1)
    M.addConstr(c+b+(1-a) >= 1)
    return c


def Xor(M, L):    
    x = Xor2(M, L[0], L[1])
    for y in L[2:]:
        x = Xor2(M, x, y)
    return x


def AND(M,a,b) :
    # 1 * 1 = 0/1
    # 1* 0 = 0/1
    # 0*0 = 0
    x = M.addVar(vtype='b')
    M.addConstr(a+b>=x)
    return x



def FeistelFunction(Model, state) :
    x= state
    y = state[5:]+state[:5]
    z= state[1:] + state[:1]

    return [Xor2(Model,z[i],AND(Model, x[i],y[i])) for i in range(len(x))]


def is_differential_possible(input, output, n_rounds,n ):
    gp.setParam("LogToConsole", 0)
    M = gp.Model()
    L = [M.addVar(vtype='b') for i in range(n)]  # var= 1 si diff #0
    R = [M.addVar(vtype='b') for i in range(n)]  # var= 1 si diff #0

    states = [[L,R,FeistelFunction(M,L)]]

    for r in range(n_rounds):
        L,R,tmp  = states[-1]
        newL = [Xor2(M,R[i],tmp[i]) for i in range(n)]
        newR = L
        newtmp = FeistelFunction(M,newL)
        states.append([newL,newR,newtmp])

    M.addConstrs(states[0][0][i] == input[0][i] for i in range(n))
    M.addConstrs(states[0][1][i] == input[1][i] for i in range(n))
    M.addConstrs(states[-1][0][i] == output[0][i] for i in range(n))
    M.addConstrs(states[-1][1][i] == output[1][i] for i in range(n))

    M.optimize()
  
    return M.Status



