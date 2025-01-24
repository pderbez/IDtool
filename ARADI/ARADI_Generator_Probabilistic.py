import gurobipy as gp
import ARADI_Validator
from ARADI import M

# Auxiliary functions

# Modelisation of the XOR of a list of 0/* . s is the output
def Xor(model, L, s):
    model.addConstr(sum(L) <= len(L) * s)
    model.addConstr(sum(L) >= s)


def ProbabilisticXOR(model, inputs, output, p) :
    L = inputs+ [output,p]
 
    with open("probaTXOR_short.esp",'r') as f :
        for line in f :
            c=0
            if line[0]!="." :
                for i in range(5) :
                    if line[i]=="0" :
                        c+=L[i]
                    elif line[i]=="1" :
                        c+=1-L[i]
                # print(line,c,L)
                model.addConstr(c>=1)


# Modelisation of the propagation of 0/* through the linear layer of round r
def L(model, state, new_state, r):
    for i in range(32):
        Xor(model, [state[j]
            for j in range(32) if M[r][i, j] == 1], new_state[i])
        
def ProbabilisticL(model, state, new_state, r,probas):
    
    for i in range(32):
        # print([j for j in range(32) if M[r][i,j] ==1])
        ProbabilisticXOR(model, [state[j]
            for j in range(32) if M[r][i, j] == 1], new_state[i],probas[i])
    # print()

# Modelisation of the propagation of the needed cells through the linear layer of round r (a cell is needed if any of the cells where it is used is needed or if the cell is active)
def Lguess(model, state, new_state, zeros, r):
    for i in range(32):
        Xor(model, [state[j] for j in range(32) if M[r]
            [j, i] == 1]+[zeros[i]], new_state[i])


# Summary trail
def getSummary(model, X, Y):
    return [getSummaryBit(model, X[i], Y[i]) for i in range(32)]


def getSummaryBit(model, a, b):
    s = model.addVar(vtype="b")
    model.addConstr(2*s <= a+b)
    model.addConstr(a+b <= 1+s)
    return s


# Description of the creation of new zeros in the  Linear Layer.
def NewZeroXor(model, L, d):
    a, b, c = L
    # d =a xor b xor c
    z = model.addVar(vtype="b")
    # If all values are already zero then no new zeros are created
    model.addConstr(a+b+c+d >= z)

    # a new zero is created if all but one value are *
    model.addConstr(a+b+c+1-d+z >= 1)
    model.addConstr(a+b+1-c+d+z >= 1)
    model.addConstr(a+1-b+c+d+z >= 1)
    model.addConstr(1-a+b+c+d+z >= 1)

    # If two values are * then no new zeros are created.
    model.addConstr(z <= 2-(a+b))
    model.addConstr(z <= 2-(a+c))
    model.addConstr(z <= 2-(a+d))
    model.addConstr(z <= 2-(b+c))
    model.addConstr(z <= 2-(b+d))
    model.addConstr(z <= 2-(c+d))
    return z


def FindNewZerosLinearLayer(model, state, new_state, r):
    return [NewZeroXor(model, [state[j] for j in range(32) if M[r][i, j] == 1], new_state[i]) for i in range(32)]


# Printing of the solutions
def getStr(model, state):
    s = "".join('.' if round(model.cbGetSolution(s))
                == 0 else '1' for s in state)
    return s


def printTrail(model, summary, backward, forward, valid, newZeros, needed_B, needed_F, proba_F, proba_B):
    rD = len(summary)-1
    rounds_b = len(backward)-len(summary)
    rounds_f = len(forward)-len(summary)

    with open(f"proba_{valid}.sol", 'w') as f:
        f.write("         FORWARD TRAIL          \t         SUMMARY TRAIL               \t      BACKWARD TRAIL  \t                        NEEDED CELLS\n")
        f.write("         (BACKWARD KR)          \t                                     \t      (FORWARD KR)  \n")
        for i in range(rounds_b):
            f.write(f"\n(key recovery) round {i} :\n")
            X = getStr(model, needed_B[i])
            P = getStr(model,proba_B[i])
            f.write(getStr(model, backward[i])+"\t" *20 + X+" "+str(X.count("1"))+" "+str(P.count("1"))+"\n")

        for i in range(rD+1):
            s = "".join('.' if round(model.cbGetSolution(s)) ==
                        0 else '1' for s in newZeros[64*i:64*(i+1)])
            s = s[:32]+"\t"+s[32:]
            f.write(f"\n(distinguisher) round {i} :")
            if "1" in s:
                f.write("\t(New zeros : " + s+")\n")
            else :
                f.write("\n")
            f.write(f"{getStr(model, backward[rounds_b+i])}\t{getStr(model, summary[i])}\t{getStr(model, forward[i])}\n")
            

        for i in range(rounds_f):
            f.write(f"\n(key recovery) round {i} :\n")
            X = getStr(model, needed_F[i+1])
            P = getStr(model,proba_F[i])
            f.write(" "*32+"\t"+" "*32+"\t"+getStr(model,forward[rD+1+i])+"\t"*3 + X+"  "+str(X.count("1"))+" "+P+"\n")


def my_callback(model, where):

    if where == gp.GRB.Callback.MIPSOL:

        model._solCount += 1

        target_i = [round(model.cbGetSolution(model._summary[0][i]))    for i in range(32)]
        target_o = [round(model.cbGetSolution(model._summary[-1][i]))   for i in range(32)]

        rD = len(model._summary) -1
        s = ARADI_Validator.is_differential_possible(target_i, target_o, rD, model._offset)

        if s == gp.GRB.INFEASIBLE:
            print(f"Found an impossible differential in {model.cbGet(gp.GRB.Callback.RUNTIME):.2f} seconds. Associated attack has complexity ={model.cbGet(gp.GRB.Callback.MIPSOL_OBJ):.2f}  ")
            printTrail(model, model._summary, model._is_zero_forward, model._is_zero_backward, f"{model._valid}_{model._offset}_{model.cbGet(gp.GRB.Callback.MIPSOL_OBJ):.2f}",
                        model._NewZeros, model._value_needed_backward, model._value_needed_forward, model._proba_forward, model._proba_backward)

            model._valid += 1

        else:
            if model._solCount % 50 == 0:
                print(f"solution {model._solCount} is possible .. we exclude it")

            c = 0
            #Remove the distinguisher from search space
            for i in range(32):
                if target_i[i] == 1:
                    c += 1-model._summary[0][i]

                if target_o[i] == 1:
                    c += 1-model._summary[-1][i]

            model.cbLazy(c >= 1)


def find_impossible_differential(rounds_b, rD, rounds_f, offset):
    model = gp.Model()
    model.setParam("LogToConsole", 0)
    model.setParam("LazyConstraints", 1)

    model._is_zero_forward = []
    model._is_zero_backward = []
    model._summary = []
    model._NewZeros = []

    model._solCount = 0
    model._valid = 0

    model._offset = offset

    model._is_zero_forward = [[model.addVar(vtype='b') for _ in range(32)]  for _ in range(rounds_b+rD+1)]
    model._is_zero_backward = [[model.addVar(vtype='b') for _ in range(32)] for _ in range(rounds_f+rD+1)]

    model._summary = [getSummary(model, model._is_zero_forward[rounds_b+i], model._is_zero_backward[i]) for i in range(rD+1)]

    model._proba_backward = [[model.addVar(vtype='b') for _ in range(32)] for _ in range(rounds_b)]
    model._proba_forward = [[model.addVar(vtype='b') for _ in range(32)] for _ in range(rounds_f)]

    model._value_needed_backward = [[model.addVar(vtype='b') for _ in range(32)] for _ in range(rounds_b+1)]
    model._value_needed_forward = [[model.addVar(vtype='b') for _ in range(32)] for _ in range(rounds_f+1)]

    # Key recovery (backward propagation)
    for r in range(rounds_b):
        ProbabilisticL(model, model._is_zero_forward[r+1], model._is_zero_forward[r], (r+offset) % 4, model._proba_backward[r])
        Lguess(model, model._value_needed_backward[r+1],  model._value_needed_backward[r], model._is_zero_forward[r], (r+offset) % 4)

    model.addConstrs(model._value_needed_backward[rounds_b][i] == 0 for i in range(32))

    # Distinguisher
    for r in range(rounds_b, rounds_b+rD):
        L(model, model._is_zero_forward[r], model._is_zero_forward[r+1], (r+offset) % 4)
        # L is involutive
        L(model, model._is_zero_backward[r+1-rounds_b], model._is_zero_backward[r-rounds_b], (r+offset) % 4)

        model._NewZeros += FindNewZerosLinearLayer(
            model, model._summary[r-rounds_b], model._summary[r+1-rounds_b], (r+offset) % 4)
        model._NewZeros += FindNewZerosLinearLayer(
            model, model._summary[r+1-rounds_b], model._summary[r-rounds_b], (r+offset) % 4)

    model.addConstrs(model._value_needed_forward[0][i] == 0 for i in range(32))

    # Key recovery (forward propagation )
    for r in range(rD, rD+rounds_f):
        ProbabilisticL(model, model._is_zero_backward[r], model._is_zero_backward[r+1], (rounds_b+r+offset) % 4, model._proba_forward[r-rD])
        Lguess(model, model._value_needed_forward[r-rD],  model._value_needed_forward[r-rD+1], model._is_zero_backward[r+1], (rounds_b+r+offset) %  4)


    # Complexity estimation
    DX = 4 * gp.quicksum(model._summary[0])
    DY = 4 * gp.quicksum(model._summary[-1])

    pb = 2*gp.quicksum(gp.quicksum(model._proba_backward[r]) for r in range(rounds_b))
    pf = 2*gp.quicksum(gp.quicksum(model._proba_forward[r]) for r in range(rounds_f))

    # model._pb = pb
    # model._pf = pf

    Din = 4 * gp.quicksum(model._is_zero_forward[0])
    Dout = 4*gp.quicksum(model._is_zero_backward[-1])

    cin = Din-DX
    cout = Dout-DY

    KinKout = 4 * (gp.quicksum(gp.quicksum(X) for X in model._value_needed_backward) +
                   gp.quicksum(gp.quicksum(X) for X in model._value_needed_forward))
    n = 4*32

    # formula = max(cin+cout - 0.5 +pb +pf , |kin u kout| - 0.5, cin + cout - 0.5 +  n + 1 - |Din| - |Dout| +pb+pf, (pb+pf+ n + 1 - 0.5 - DY +  cin )/2)
    Term1, Term2, Term3, Term4, complexity, kin, kout = [
        model.addVar(vtype=gp.GRB.CONTINUOUS) for _ in range(7)]
    model.addConstr(Term1 == cin+cout - 0.53 +pb+pf)
    model.addConstr(Term2 == KinKout - 0.53)
    model.addConstr(Term3 == cin+cout - 0.53+n+1 - Din-Dout +pb+pf)
    model.addConstr(Term4 == (-0.53+n+1-pb+pf -DY +cin)/2)

    model.addConstr(complexity >= Term1)
    model.addConstr(complexity >= Term2)
    model.addConstr(complexity >= Term3)
    model.addConstr(complexity >= Term4)
    
   # model.addConstr(complexity <=256)
    model.addConstr(gp.quicksum(model._NewZeros) >= 1)

    model.setObjective(complexity)
    model.addConstr(kin == gp.quicksum(gp.quicksum(X)
                for X in model._value_needed_backward))
    model.addConstr(kout == gp.quicksum(gp.quicksum(X)
                for X in model._value_needed_forward))
    model.optimize(my_callback)

    try:
        print(f"cin+cout - 0.5 +pf+pf = {Term1.X}, |kin u kout| - 0.5 = {Term2.X}, cin + cout - 0.5 +  n + 1 - |Din| - |Dout| +pb+pf ={Term3.X}, (pb+pf+ n + 1 - 0.5 - DY +  cin )/2 = {Term4.X}" )
        print(f"============= {rD} rounds == ARADI ==  Explored {model._solCount} solutions and found {model._valid} ID in {model.Runtime:.2f} seconds ==========")
    except:
        pass


for offset in range(0, 4):
    print(f"============= offset = {offset} ========")
    find_impossible_differential(3, 7, 2, offset)
