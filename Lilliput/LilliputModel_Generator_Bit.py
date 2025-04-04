from gurobipy import *
import Lilliput_Validator


pi = [13, 9, 14, 8, 10, 11, 12, 15, 4, 5, 3, 1, 2, 6, 0, 7]
pi = [pi.index(i) for i in range(16)]


N = 64



## Encoding three state values in two bits
#(0,0) : inactive bit
#(0,1) : difference =1
#(1,1) : unknown
from gurobipy import *
def create_var(model,name="") :
    a = model.addVar(vtype="b",name=name+"0")
    b = model.addVar(vtype="b",name=name+"0")
    model.addConstr(a<=b)
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

def XorList(M, L, s=None):
    if len(L)==1 :
        return L[0]

    return XORvar(M, L[0],XorList(M,L[1:]))
 
def arbitrary_sbox(M,inputs) :

    m = len(inputs)
    outputs= [create_var(M,name='sbox') for _ in range(m)]
    full_zero = M.addVar(vtype="b")

    b = sum(x[0]+x[1] for x in inputs)
    c = sum(x[0]+x[1] for x in outputs)

    M.addConstr(full_zero +b  >=  1)
   
    for x in outputs :
        M.addConstr(full_zero + x[0] >=1 )
        M.addConstr(full_zero + x[1] >=1)

    M.addConstr( 2*m*(1-full_zero) >= b)
    M.addConstr( 2*m*(1-full_zero) >=c)


    return outputs


def RoundFunction(M, state):
    tmp_state = []
    for i in range(8) :   
        tmp_state+=arbitrary_sbox(M, state[4*i:4*i+4])
    

    Left_State_afterSbox = state[:32] + [XORvar(M,tmp_state[N-4*(j//4+1)+j%4], state[j]) for j in range(N//2,N)]
    for j in range(4)   :
        Left_State_afterSbox[60+j] = XorList(M, [ Left_State_afterSbox[60+j]]+ [state[4*i+j] for i in range(1,8)] )
    
    for k in range(9,15) :
        for j in range(4) :
            Left_State_afterSbox[4*k+j] = XORvar(M, Left_State_afterSbox[4*k+j], state[28+j])

    new_state= Left_State_afterSbox
    return [new_state[4*pi[i//4]+i%4] for i in range(N)]


def InverseRoundFunction(M, state):
    state = [state[4*pi.index(i//4)+i%4] for i in range(N)]

    tmp_state = []
    for i in range(8) :
        tmp_state+=arbitrary_sbox(M, state[4*i:4*i+4])
   

    Left_State_afterSbox = state[:32] + [XORvar(M,tmp_state[N-4*(j//4+1)+j%4], state[j]) for j in range(N//2,N)]
    for j in range(4)   :
        Left_State_afterSbox[60+j] = XorList(M, [ Left_State_afterSbox[60+j]]+ [state[4*i+j] for i in range(1,8)] )
    
    for k in range(9,15) :
        for j in range(4) :
            Left_State_afterSbox[4*k+j] = XORvar(M, Left_State_afterSbox[4*k+j], state[28+j])

    return Left_State_afterSbox

def getSummaryBit(M, A,B):
    a = M.addVar(vtype="b")
    b = M.addVar(vtype="b")
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
                M.addConstr(c>=1)
    return (a,b)


def getSummary(M, X, Y):
    return [getSummaryBit(M, X[i], Y[i]) for i in range(N)]


def isConstradiction(M,A) :
    x = M.addVar(vtype="b")
    M.addConstr(A[0]+A[1]>=x)
    M.addConstr(A[0]+1-A[1]>=x)
    M.addConstr(2-A[0]-A[1]>=x)
    M.addConstr(1-A[0]+A[1]+x>=1)
    return x

def NewZeroXor(M, L ) :
    assert len(L) ==3

    z = M.addVar(vtype="b")
    L=list(L[0])+list(L[1])+list(L[2])+[z]
    with open("NewZeroXor_short.esp",'r') as file :
        for line in file :
            if line[0]!="." :
                c=0
                for i in range(7) :
                    if line[i]=='1' :
                        c+= 1-L[i]
                    elif line[i]=='0' :
                        c+= L[i]
                M.addConstr(c>=1)
    return z

def new_zeros(M, state_in, state_out) :
    tmp_state = []
    for i in range(8) :   
        tmp_state+=arbitrary_sbox(M, state_in[4*i:4*i+4])
   
    state_out = [state_out[4*pi.index(i//4)+i%4] for i in range(N)]

    New_zeros = []
    for j in range(4) :
        New_zeros.append(NewZeroXor(M, [state_out[32+j], state_in[32+j], tmp_state[28+j]] ))

    # for k in range(9,15) :
    #     for j in range(4) :
    #         New_zeros.append(NewZeroXor(M, [state_out[4*k+j],state_in[28+j], tmp_state[N-4*(k+1)+j], state_in[4*k+j] ] ))

    # for j in range(4) :
    #     New_zeros.append(NewZeroXor(M, [state_out[60+j], state_in[60+j], tmp_state[j]]+ [state_in[4*k+j] for k in range(1,8)]))
    
    return New_zeros[::-1]

def getStr(x) :
    try :
        x= (round(x[0].Xn) , round(x[1].Xn))
    except :
        pass
    dic = {(0,0):"0", (0,1):"1", (1,0):"X",(1,1):"*"}
    return dic[x]


def my_callback(model, where):

    if where == GRB.Callback.MIPSOL:
        model._solCount += 1

        target_i = [(round(model.cbGetSolution(model._summary[0][i][0])), round(model.cbGetSolution(model._summary[0][i][1])))
                    for i in range(64)]
        target_o = [(round(model.cbGetSolution(model._summary[-1][i][0])), round(model.cbGetSolution(model._summary[-1][i][1])))
                    for i in range(64)]

        rD = len(model._summary)
        # nb_one = sum(target_i[0])+sum(target_i[1])+sum(target_o[0])+sum(target_o[1])
        
   
        s =Lilliput_Validator.is_differential_possible(
            target_i, target_o, rD-1)

        if s == GRB.INFEASIBLE:
            model._valid +=1 
            print(f"{model._valid} Found an impossible differential provoked by {round(sum(model.cbGetSolution(model._NewZeros)))} zeros. ",
                  model.cbGet(GRB.Callback.RUNTIME))
            
            try : 
                input = "".join([hex(int("".join(getStr(x) for x in target_i[4*i:4*i+4]),base=2))[2:] for i in range(16)])[::-1]
                output = "".join([hex(int("".join(getStr(x) for x in target_o[4*i:4*i+4]),base=2))[2:] for i in range(16)])[::-1]
                
                print("ID:", input[:8], input[8:],
                    " -/->  " + output[:8], output[8:])
            except :
                print("ID:", "".join([getStr(x) for x in target_i])[::-1],
                    " -/->  ",  "".join([getStr(x) for x in target_o])[::-1])
            

        else:
            print(f"solution {model._solCount} is possible .. we exclude it")

            c = 0
            for i in range(len(target_i)):
                c += (1-model._summary[0][i][0])*round(target_i[i][0])+ model._summary[0][i][0]*(1-round(target_i[i][0]))
                c += (1-model._summary[0][i][1])*round(target_i[i][1])+ model._summary[0][i][1]*(1-round(target_i[i][1]))
                c += (1-model._summary[-1][i][0])*round(target_o[i][0])+ model._summary[-1][i][0]*(1-round(target_o[i][0]))
                c += (1-model._summary[-1][i][1])*round(target_o[i][1])+ model._summary[-1][i][1]*(1-round(target_o[i][1]))
             
             
             

            model.cbLazy(c >= 1)

def isActiveCell(M,input) :
    z = M.addVar(vtype="b")
    M.addConstr(4*z>=sum(x[1] for x in input))

    return z


def find_impossible_differential(rD):
    M = Model()
    M.setParam("LazyConstraints", 1)

    M._is_zero_forward = [[create_var(M,name="initf") for _ in range(N)]]
    M._is_zero_backward = [[create_var(M,name="initb") for _ in range(N)]]

    M._solCount = 0
    M._valid = 0

    for r in range(rD):
        M._is_zero_forward.append(RoundFunction(M, M._is_zero_forward[-1]))
        M._is_zero_backward = [InverseRoundFunction(
            M, M._is_zero_backward[0])]+M._is_zero_backward


    M._summary = [ getSummary(M, M._is_zero_forward[r], M._is_zero_backward[r]) for r in range(rD+1)]
    M._NewZeros =  []
    for r in range(rD) :
        M._NewZeros+= new_zeros(M, M._summary[r], M._summary[r+1])

    # M.addConstr(sum(isConstradiction(M,x) for x in M._summary[0]+ M._summary[-1])<=0)
    M.addConstr(4*sum(isConstradiction(M,x)  for L in M._summary for x in L) + sum(M._NewZeros) >=4)    

    # M.setObjective(sum(x[0]+x[1] for x in M._summary[0])+sum(x[0]+x[1] for x in M._summary[-1]) , GRB.MAXIMIZE)

    M.addConstr(sum(x[0] for x in M._summary[0]+ M._summary[-1])<=0)

    M.addConstr(sum(isActiveCell(M,M._summary[0][4*i:4*(i+1)]) for i in range(16))<=1)
    M.addConstr(sum(isActiveCell(M,M._summary[-1][4*i:4*(i+1)]) for i in range(16))<=1)
    M.setParam("PoolSearchMode",2)
    M.setParam("PoolSolutions",250) 
    M.setParam("LogToConsole",1)
    # M.Params.SolFiles = 'Lilliput'

    # M.addConstr(sum(x[0]+x[1] for x in M._summary[0])==1)
    # M.addConstr(M._summary[0][48][0]+M._summary[0][51][1]==1)

    # M.addConstr(sum(x[0]+x[1] for x in M._summary[-1])==1)
    # M.addConstr(M._summary[-1][4][0]+M._summary[-1][4][1]==1)

    M.optimize(my_callback)
    for r in range(rD+1):
        # s1="".join([str(round(x.X)) for x in M._is_zero_forward[r][::-1]])
        # s2 ="".join([str(round(x.X)) for x in M._is_zero_backward[r][::-1]])
        s1="".join([getStr(x) for x in M._is_zero_forward[r][::-1]])
        s2="".join([getStr(x) for x in M._is_zero_backward[r][::-1]])
        s3="".join([getStr(x) for x in M._summary[r][::-1]])
        s ="|".join([s3[4*i:4*i+4] for i in range(16)])
        n=len(s)

        print(s[:n//2], s[n//2:], [round(x.X) for x in M._NewZeros[4*r: 4*r+4]])


find_impossible_differential(9)
