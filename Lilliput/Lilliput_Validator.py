from gurobipy import *
setParam("LogToConsole",0)

pi = [13, 9, 14, 8, 10, 11, 12, 15, 4, 5, 3, 1, 2, 6, 0, 7]
pi = [pi.index(i) for i in range(16)]


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


def Round(M,state) :

    afterSbox = []
    for i in range(8) :
        afterSbox+= Sbox(M,state[4*i:4*i+4])
    new_state = state[:32]+ [Xor2(M,state[i], afterSbox[64-4*(i//4+1)+i%4]) for i in range(32,64)]

    for i in range(4) :
        new_state[60+i] = Xor(M, [new_state[60+i]]+[state[4*k+i] for k in range(1,8)])

    for k in range(9,15) :
        for i in range(4) :
            new_state[4*k+i] = Xor2(M,new_state[4*k+i], state[28+i])

    
    return [new_state[4*pi[i//4]+i%4] for i in range(64)]
    

def Sbox(M,input):
    output = [M.addVar(vtype="b")for _ in range(4)]
  
    L = input+output
    
    with open("S_lilliputDiff_short.esp",'r') as file :
        for line in file :
            if line[0]!="." :
                c=0
                for i in range(8) :
                    if line[i]=='1' :
                        c+= 1-L[i]
                    elif line[i]=='0' :
                        c+= L[i]
                M.addConstr(c>=1)
    return output
    

def is_differential_possible(target_i, target_o, rD) :
    M= Model()

    state = [[M.addVar(vtype="b") for _ in range(64)]]

    for r in range(rD) :
        state.append(Round(M,state[-1]))

    # print(target_i)
    for i in range(64) :
        if target_i[i][0]==target_i[i][1]==0 :
            M.addConstr(state[0][i]==0)

        elif target_i[i]==(0,1) :
            M.addConstr(state[0][i]==1)

        if target_o[i][0]==target_o[i][1]==0 :
            M.addConstr(state[-1][i]==0)

        elif target_o[i]==(0,1) :
            M.addConstr(state[-1][i]==1)

    M.optimize()

    # for r in range(len(state)) :
    #     s= "|".join(["".join([str(round(x.X)) for x in state[r][4*i:4*i+4]]) for i in range(16)])[::-1]
    #     print(r,s[:len(s)//2], s[len(s)//2:])

    return M.Status