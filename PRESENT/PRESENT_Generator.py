import gurobipy as gp
import PRESENT_Validator
from draw_PRESENT import draw

gp.setParam("LogToConsole", 1)



def getStr(model, x):
    if round(model.cbGetSolution(x)) == 0:
        return "."
    else:
        return "*"


def printTrail(M, A,B,C,N, n ):
    name = f"Present_{n}.sol"
    f = open(name,"w")
    r=1
    for i in range(len(A)) :
        f.write(f"Round {r}\n")

        f.write("".join(getStr(M,A[i][0][j]) for j in range(64))+ "   "+ "".join(getStr(M,B[i][0][j]) for j in range(64)) +  "   "+ "".join(getStr(M,C[i][0][j]) for j in range(64))+"\n")
        f.write("".join(getStr(M,A[i][1][j]) for j in range(64))+ "   "+ "".join(getStr(M,B[i][1][j]) for j in range(64)) +  "   "+ "".join(getStr(M,C[i][1][j]) for j in range(64)) + "  "+"".join([str(round(M.cbGetSolution(n))) for n in N[16*i:16*i+16]])+"\n\n")
        r+=1

    f.close()

def getSummaryBit(M, a, b):
    # 0+0 =0 , *+0 = 0 , *+* = *
    # Non 0,0,*
    # Non 0,_ 1
    s = M.addVar(vtype="b")
    M.addConstr(2* s <= a +b)
    M.addConstr(a+b <= 1+s)
    return s


def getSummary(M, X, Y):
    return [getSummaryBit(M, X[i], Y[i]) for i in range(64)]


P = [16*(i % 4)+i//4 for i in range(64)]

Pinv = [P.index(i) for i in range(64)]


def PLayer(state):
    new_state = [state[Pinv[i]] for i in range(64)]
    return new_state


def SboxLayerFirst(M, state, new_state):


    for i in range(16):
        cell = state[4*i:4*i+4]
        new_cell = new_state[4*i:4*i+4]
      
        L = cell+new_cell
        with open("S_PRESENT_Semi_Min_Diff_short.esp", 'r') as f:
            for line in f:
                if line[0] != '.':
                    c = 0
                    for i in range(8):
                        if line[i] == '0':
                            c += L[i]
                        elif line[i] == '1':
                            c += 1-L[i]

                    M.addConstr(c >= 1)


def SboxLayerLast(M, state, new_state):
    

    for i in range(16):
        cell = state[4*i:4*i+4]
        new_cell = new_state[4*i:4*i+4]
        # M.update()
        L = cell+new_cell
        with open("S_PRESENT_INV_Semi_Min_Diff_short.esp", 'r') as f:
            for line in f:
                if line[0] != '.':
                    c = 0
                    for i in range(8):
                        if line[i] == '0':
                            c += L[i]
                        elif line[i] == '1':
                            c += 1-L[i]
                    M.addConstr(c >= 1)

                    # print(c)


def SboxLayer(M, state, new_state):
    #  Arbitray sboxes

    for i in range(16):
        cell = state[4*i:4*i+4]
        new_cell = new_state[4*i:4*i+4]
        full_zero = M.addVar(vtype="b")
        
        M.addConstr(4*(full_zero) >= sum(cell) )
        M.addConstr(sum(cell) >= full_zero)
        for x in new_cell:
            M.addConstr(full_zero >= x)
        M.addConstr(sum(new_cell) >= 4*(full_zero))



def FindNewZerosSboxes(M, Known_zeros_before, Known_zeros_after):
    NewZero = M.addVar(vtype='b', name="SboxNewZero")
    L = Known_zeros_before + Known_zeros_after+[NewZero]
    with open("S_Present_short.esp", 'r') as f:
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
    return [FindNewZerosSboxes(M, X[4*i:4*i+4], Y[4*i:4*i+4]) for i in range(16)]


def my_callback(model, where):

    if where == gp.GRB.Callback.MIPSOL:

        model._solCount += 1


        target_i = [round(model.cbGetSolution(model._summary[0][0][i]))
                    for i in range(64)]
        target_o = [round(model.cbGetSolution(model._summary[-1][1][i]))
                    for i in range(64)]
        newZeros = [round(model.cbGetSolution(model._NewZeros[i]))
                    for i in range(len(model._NewZeros))]
        
        rD = len(model._summary)


        # print("...", r, target_i, target_o)
        s = PRESENT_Validator.is_differential_possible(target_i, target_o, rD)

        if  s == gp.GRB.INFEASIBLE:
            print(f"Found an impossible differential provoked by {round(sum(model.cbGetSolution(model._NewZeros)))} zeros with {(sum(target_i) + sum(target_o))} active bits")
            print("ID:", target_i, target_o)
           
            draw( f"sol/Present_{model._valid}_{sum(target_i) + sum(target_o)}.tex", model)

            model._valid += 1

     
        else:
            if model._solCount %50 ==0 :
                print(f"solution {model._solCount} is possible .. we exclude it")

            c = 0
            for i in range(64):
                if round(model.cbGetSolution(model._summary[0][1][i])) == 1:
                    c += 1-model._summary[0][1][i]
                if round(model.cbGetSolution(model._summary[-1][0][i])) == 1:
                    c += 1-model._summary[-1][0][i]

        
            if not c is 0 and model._valid <100 :
                model.cbLazy(c >= 1)


        # print()

         



def find_impossible_differential(rD):
    M = gp.Model()
    M.setParam("LazyConstraints", 1)

    M._is_zero_forward = []
    M._is_zero_backward = []
    M._summary = []
    M._NewZeros = []

    M._solCount = 0
    M._valid = 0

    init_dist_forward = [M.addVar(vtype='b') for _ in range(64)]
    init_dist_backward = [M.addVar(vtype='b') for _ in range(64)]



    # Distinguisher
    for r in range(rD):
       
        after_S_forward = [M.addVar(vtype='b') for _ in range(64)]
        after_S_backward = [M.addVar(vtype='b') for _ in range(64)]
        M._is_zero_forward.append([init_dist_forward, after_S_forward])
        M._is_zero_backward.append([init_dist_backward,after_S_backward])

        if r+1<rD :
            SboxLayer(M, after_S_backward, init_dist_backward)
        if r+1==rD :
            SboxLayerLast(M, after_S_backward, init_dist_backward)

        M._summary.append([None, getSummary( M, M._is_zero_forward[r][1], M._is_zero_backward[r][1])])
       
        if r>=1 :
            SboxLayer(M, init_dist_forward, after_S_forward)
        else :
            SboxLayerFirst(M, init_dist_forward, after_S_forward)        
            

        init_dist_forward=PLayer(M._is_zero_forward[r][1])
        init_dist_backward=PLayer(M._is_zero_backward[r][1])


    M._summary[0][0] = getSummary(M,M._is_zero_forward[0][0], M._is_zero_backward[0][0])
    for r in range(rD) :
        if r+1<rD :
            M._summary[r+1][0] = PLayer(M._summary[r][1])
        M._NewZeros += FindNewZeros(M, M._summary[r][0], M._summary[r][1])


    M.addConstr(gp.quicksum(M._NewZeros)>=1)

    # M.setObjective(-(gp.quicksum(M._is_zero_forward[0][1])+gp.quicksum(M._is_zero_backward[-1][0])  ))

 
    M.optimize(my_callback)
    
    print(f"============= {rD} rounds == Present ==  Explored {
          M._solCount} solutions and found {M._valid} ID in { round(M.Runtime,2)} seconds ==========")
   

find_impossible_differential(6)
