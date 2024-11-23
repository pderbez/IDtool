import gurobipy as gp


def getStr(x):
    if round(x.X) == 0:
        return "."
    else:
        return "*"


def printTrail(states):
    r=1
    for current_state in states:
        print(f"Round {r}")

        print("".join(getStr(current_state[0][j]) for j in range(64)))
        print("".join(getStr(current_state[1][j]) for j in range(64)))
        print()
        r+=1

P = [16*(i%4)+i//4 for i in range(64)]

Pinv = [P.index(i) for i in range(64)]
def PLayer(state) :
    new_state = [state[Pinv[i]] for i in range(64)]
    return new_state

def SboxLayer(Model, state) :
    new_state = [Model.addVar(vtype='b') for i in range(64)]
    for i in range(16) :
        cell = state[4*i:4*i+4]+new_state[4*i :4*i+4]
        with open("S_PRESENTDiff_short.esp",'r') as f :
            for line in f :
                c=0
                if line[0]!="." :
                    for x in range(8) :
                        if line[x]=="0" :
                            c+= cell[x]
                        elif line[x]=="1":
                            c+= 1-cell[x]
                    Model.addConstr(c>=1)

    return new_state


def getModel(input,output, n_rounds) :
    M = gp.Model()
    state = [M.addVar(vtype='b') for i in range(64)]  # var= 1 si diff #0
    states = [[state, SboxLayer(M,state)]]
    state = states[-1][-1]
 
    for r in range(n_rounds-1):
      
        state =  PLayer(state)
        states.append([state,SboxLayer(M,state)])
        state = states[-1][-1]

    for i in range(16) :
        if sum(input[4*i:4*i+4]) ==4 :
            M.addConstr(gp.quicksum(states[0][1][4*i:4*i+4])>=1)
        else :
            for j in range(4) :
                if input[4*i+j] >=0 :
                    M.addConstr(states[0][0][4*i+j] == input[4*i+j] )
            
        

        if sum(output[4*i:4*i+4]) ==4 :
            M.addConstr(gp.quicksum(states[-1][0][4*i:4*i+4])>=1)
        else :
            for j in range(4) :
                if output[4*i+j] >=0 :
                    M.addConstr(states[-1][1][4*i+j] == output[4*i+j] )
               

    return M,states

def is_differential_possible(input, output, n_rounds):
    gp.setParam("LogToConsole", 0)
    M,states = getModel(input,output,n_rounds)
   
    M.optimize()      
        
    return M.Status


def getSymbol(x) :
    if x==0  or x==1:
        return str(x)
    else :
        return "*"
    
if __name__ =="__main__" :
    # # Test 1 : 
    # input = [0 for i in range(64)]
    # output = [0 for i in range(64)]
    # print(is_differential_possible(input, output, 10) == gp.GRB.OPTIMAL)

    # # Test 2 : 
    # input = [1 for i in range(64)]
    # output = [1 for i in range(64)]
    # print(is_differential_possible(input, output, 10) == gp.GRB.OPTIMAL)

    # # Test 3 : Tezcan 2014
    input = [0]*64
    for x in [8,11,24,27]: 
        input[x] = 1
    output = [1]*16+[0]*16+[0]+[1]*15+[0]*16
    print(is_differential_possible(input, output, 6) == gp.GRB.INFEASIBLE)

   



