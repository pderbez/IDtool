## Encoding three state values in two bits
#(0,0) : inactive bit
#(0,1) : difference =1
#(1,1) : unknown
from gurobipy import *
def create_var(model) :
    a = model.addVar(vtype="b")
    b = model.addVar(vtype="b")
    model.addConstr(a<=b)
    return (a,b)

def ANDvar(model,A,B) :
    a,b = create_var(model)
    model.addConstr(a==b)
    model.addConstr(4*a >= A[0]+A[1]+ B[0]+B[1])
    model.addConstr(a <=  A[0]+A[1]+ B[0]+B[1])
    return (a,b)

def XORvar(model,A,B) :
    C = create_var(model)
    model.addConstr(2*C[0] >= A[0]+B[0])
    model.addConstr(C[0] <= A[0]+ B[0])
    model.addConstr(A[1]+B[1]+A[0]+B[0]>=C[1])
    model.addConstr(2-A[1]-B[1]+A[0]+B[0]>=C[1])
    model.addConstr(A[0]+B[0]<=2*C[1])
    model.addConstr(1-A[1]+B[1]+A[0]+B[0]+C[1]>=1)
    model.addConstr(A[1]+1-B[1]+A[0]+B[0]+C[1]>=1)
    return C

def MergeOrContradictVar(model,A,B) :
    a = model.addVar(vtype="b")
    b = model.addVar(vtype="b")
    L = list(A)+list(B)+[a,b]
    with open("Merge.esp",'r') as file :
        for line in file :
            if line[0]!="." :
                c=0
                for i in range(6) :
                    if line[i]=='1' :
                        c+= 1-L[i]
                    elif line[i]=='0' :
                        c+= L[i]
                model.addConstr(c>=1)
    return (a,b)

def printvar(A) :
    if round(A[0].X) == 0 :
        if round(A[1].X) ==0:
            return '0'
        else :
            return '1'
    else :
        if round(A[1].X)==0 :
            return 'X'
        return '?'
    
def setVar(M,x) :
    A = create_var(M)
    if x==0 :
        M.addConstr(A[0]==0)
        M.addConstr(A[1]==0)
    elif x==1 :
        M.addConstr(A[0]==0)
        M.addConstr(A[1]==1)
    else :
        M.addConstr(A[0]==1)
        M.addConstr(A[1]==1)
    return A

def XORState(M,x,y) :
    return [XORvar(M,x[i],y[i]) for i in range(len(x))]

def ANDState(M,x,y) :
    return [ANDvar(M,x[i],y[i]) for i in range(len(x))]


def MergeOrContradictState(M,x,y) :
    return [MergeOrContradictVar(M,x[i],y[i]) for i in range(len(x))]

def printState(x) :
    if x is not None :
        return "".join(printvar(a) for a in x[0])+ "  "+ "".join(printvar(a) for a in x[1])
    else : 
        return ""

def printMerge(a,b) :

    s=""
    for i in range(len(a)):
        if printvar(a[i])==printvar(b[i]) :
            s+=printvar(a[i])
        else :
            if printvar(a[i])=="?" :
                s+=printvar(b[i])
            if printvar(b[i])=="?":
                s+=printvar(a[i])
            else :
                s+"X" 

    return s

def isConstradiction(M,A) :
    x = M.addVar(vtype="b")
    M.addConstr(A[0]+A[1]>=x)
    M.addConstr(A[0]+1-A[1]>=x)
    M.addConstr(2-A[0]-A[1]>=x)
    M.addConstr(1-A[0]+A[1]+x>=1)
    return x

def FeistelFunction(M, state):
    x = state
    y = state[5:]+state[:5]
    z = state[1:] + state[:1]    
    a =  ANDState(M, x, y)

    return XORState(M, z, a),a



def SIMECK(r,n,rm, input=None, output=None):
    M= Model()
    forward_state = [[[create_var(M) for _ in range(n)], [create_var(M) for _ in range(n)]]]
    
    if input is not None :
        for a in range(2) :
            for i in range(n) :
                forward_state[0][a][i] =setVar(M,input[a][i])
    


    backward_state = [[[create_var(M) for _ in range(n)], [create_var(M) for _ in range(n)]]]
    
    if output is not None :
        for a in range(2) :
            for i in range(n) :
                backward_state[0][a][i] = setVar(M,output[a][i])
    

    TMP = []
    for rr in range(r) :
        tmp ,a = FeistelFunction(M,forward_state[-1][0])
        TMP.append(a)
        forward_state.append([XORState(M,forward_state[-1][1], tmp), forward_state[-1][0]])

        tmp,a = FeistelFunction(M,backward_state[0][1]) 
        backward_state = [[backward_state[0][1] , XORState(M,backward_state[0][0],tmp)]]+ backward_state

    


    FirstMergeTrail = [[MergeOrContradictState(M,forward_state[rr][0], backward_state[rr][0]), MergeOrContradictState(M,forward_state[rr][1], backward_state[rr][1])] for rr in range(r+1)]
    SecondMergeTrail = [None for _ in range(r+1)]
    
    SecondMergeTrail[rm+1] = FirstMergeTrail[rm+1]
    for rr in range(rm+2,r+1) :
        tmp ,a = FeistelFunction(M, SecondMergeTrail[rr-1][0])
        PropagateMerge = [XORState(M,SecondMergeTrail[rr-1][1], tmp), SecondMergeTrail[rr-1][0]]
        SecondMergeTrail[rr] = [MergeOrContradictState(M,FirstMergeTrail[rr][0], PropagateMerge[0]), MergeOrContradictState(M,FirstMergeTrail[rr][1], PropagateMerge[1])] 

    
    for rr in range(rm, -1, -1) :
        tmp ,a = FeistelFunction(M, SecondMergeTrail[rr+1][1])
        PropagateMerge = [SecondMergeTrail[rr+1][1], XORState(M,SecondMergeTrail[rr+1][0], tmp)]
        SecondMergeTrail[rr] = [MergeOrContradictState(M,FirstMergeTrail[rr][0], PropagateMerge[0]), MergeOrContradictState(M,FirstMergeTrail[rr][1], PropagateMerge[1])] 



    Contradictions = []
    for rr in range(r+1) :
        for a in range(2) :
            for i in range(n) :
                Contradictions.append(isConstradiction(M,FirstMergeTrail[rr][a][i]))
                Contradictions.append(isConstradiction(M,SecondMergeTrail[rr][a][i]))


    # M.setObjective(-sum(Contradictions))
    M.optimize()
    
    if sum(x.X for x in Contradictions) >0 :
        for rr in range(r+1) :
        #     # print(printState(MergeTrail[rr]))
            print(printState(forward_state[rr]), printState(backward_state[rr]), printState(FirstMergeTrail[rr]), printState(SecondMergeTrail[rr]))

    return sum(x.X for x in Contradictions)
# SIMECK(17,32, 6)



### Test

# M=Model()
# M.setParam("LogToConsole",0)
# A =setVar(M,0)
# B= setVar(M,1)
# E = setVar(M,-1)

# C=XORvar(M,A,B)
# D=ANDvar(M,A,B)
# M.optimize()
# print(printvar(A), printvar(B), printvar(C), printvar(D))

# C=XORvar(M,B,A)
# D=ANDvar(M,B,A)
# M.optimize()
# print(printvar(B), printvar(A), printvar(C), printvar(D))

# C=XORvar(M,A,A)
# D=ANDvar(M,A,A)
# M.optimize()
# print(printvar(A), printvar(A), printvar(C), printvar(D))

# C=XORvar(M,B,B)
# D=ANDvar(M,B,B)
# M.optimize()
# print(printvar(B), printvar(B), printvar(C), printvar(D))


# C=XORvar(M,A,E)
# D=ANDvar(M,A,E)
# M.optimize()
# print(printvar(A), printvar(E), printvar(C), printvar(D))


# C=XORvar(M,E,A)
# D=ANDvar(M,E,A)
# M.optimize()
# print(printvar(E), printvar(A), printvar(C), printvar(D))
