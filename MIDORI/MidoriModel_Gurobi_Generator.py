##  In this code, the convention is inverse : a variable is 1 if it is inactive, and 0 if unknown. 
##  It is possible to look for zeros around the S-box but this option is currently desactivated (line 280)


from gurobipy import *
from MidoriModel_Gurobi_Todo import Midori_diff
from draw_Midori import draw

pi = [0, 10, 5, 15, 14, 4, 11, 1, 9, 3, 12, 6, 7, 13, 2, 8]


def xorList(model,L,s=None) :
    if s is None :
        s = model.addVar(vtype="b")
    for x in L :
        model.addConstr(x>=s)
    model.addConstr(s>=sum(L)-len(L)+1)
    return s


def MixColumn(model,L1,L2) :
    xorList(model,[L1[1],L1[2],L1[3]],L2[0])
    xorList(model,[L1[0],L1[2],L1[3]],L2[1])
    xorList(model,[L1[0],L1[1],L1[3]],L2[2])
    xorList(model,[L1[0],L1[1],L1[2]],L2[3])


def OrList(model,List,res=None) :
    if res is None :
        res = model.addVar(vtype="b")
    for x in List :
        model.addConstr(res>=x)
    model.addConstr(sum(List)>=res)
    return res



def FindNewZerosMixColumn(model, Known_zeros_before, Known_zeros_after) :
    newZeros = []
    # for i in range(4) :
    #     # TODO (considérer cela comme une Sbox)
    #     newZeros.append(NewZeroMixColumn(model,i,Known_zeros_before,Known_zeros_after))
    #     newZeros.append(NewZeroMixColumn(model,i,Known_zeros_after,Known_zeros_before))

        
    NewZero = model.addVar(vtype='b',name="MixColumn")
    L= Known_zeros_before+ Known_zeros_after+[NewZero]
    with open("MC_Midori_fin.esp",'r') as f :
        for line in f :
            c = 0
            for i in range(9) :
                if line[i] =='0' :
                    c+= L[i]
                elif line[i] =='1' :
                    c+= 1-L[i]
            model.addConstr(c>=1)

    newZeros.append(NewZero)
    return newZeros

def Differences_on_full_cells(model,L,i) :
   
    if i==0 :
        #*0*00*0* -> *0*00*0*
        #0*0**0*0 -> 0*0**0*0
        I = [4,1,6,3]
        J = [0,5,2,7]
       
    
    elif i==1 : 
        # **0000** -> **0000**
        # 00****00 -> 00****00

        I = [1,6,7,0]
        J = [5,2,3,4]

      
    
    elif i==2:
        # *0000*** -> *0000***
        # 0****000 -> 0****000
        I = [2,3,4,1]
        J = [6,7,0,5]
       

    else :
        # *00*0**0 -> *00*0**0
        # 0**0*00* -> 0**0*00*
        I = [7,4,1,2]
        J = [3,0,5,6]
       
    for x in I[1:]:
        model.addConstr(L[I[0]]==L[x])
    for x in J[1:] :
        model.addConstr(L[J[0]]==L[x])

def SubCell(model,i, L1,L2=None) :
    if L2 is None :
        L2 = [model.addVar(vtype='b') for i in range(len(L1))]
    
    if i==0 :
        #*0*00*0* -> *0*00*0*
        #0*0**0*0 -> 0*0**0*0
        I = [4,1,6,3]
        J = [0,5,2,7]
       
    
    elif i==1 : 
        # **0000** -> **0000**
        # 00****00 -> 00****00

        I = [1,6,7,0]
        J = [5,2,3,4]

      
    
    elif i==2:
        # *0000*** -> *0000***
        # 0****000 -> 0****000
        I = [2,3,4,1]
        J = [6,7,0,5]
       

    else :
        # *00*0**0 -> *00*0**0
        # 0**0*00* -> 0**0*00*
        I = [7,4,1,2]
        J = [3,0,5,6]

    L1a = [L1[x] for x in I]
    L1b = [L1[x] for x in J]

    L2a = [L2[x] for x in I]
    L2b = [L2[x] for x in J]

    SubSubCell(model,L1a,L2a)
    SubSubCell(model,L1b,L2b)

    return L2

def SubSubCell(model,L1,L2) :
    full_zero = model.addVar(vtype='b',name="FULLZERO")
    model.addConstr(full_zero >=  sum(L1) - 3 )
    model.addConstr( sum(L1)>= 4*full_zero)
    for x in L2:
        model.addConstr(full_zero >=  x )
    model.addConstr( sum(L2)>= 4*full_zero)

def FindNewZeroSubCell(model, i,L1,L2) :
    
    if i==0 :
        #*0*00*0* -> *0*00*0*
        #0*0**0*0 -> 0*0**0*0
        I = [4,1,6,3]
        J = [0,5,2,7]
       
    
    elif i==1 : 
        # **0000** -> **0000**
        # 00****00 -> 00****00

        I = [1,6,7,0]
        J = [5,2,3,4]

      
    
    elif i==2:
        # *0000*** -> *0000***
        # 0****000 -> 0****000
        I = [2,3,4,1]
        J = [6,7,0,5]
       

    else :
        # *00*0**0 -> *00*0**0
        # 0**0*00* -> 0**0*00*
        I = [7,4,1,2]
        J = [3,0,5,6]

    L1a = [L1[x] for x in I]
    L1b = [L1[x] for x in J]

    L2a = [L2[x] for x in I]
    L2b = [L2[x] for x in J]
    NewZeros = NewZerosSubSubCell(model,L1a,L2a)+NewZerosSubSubCell(model,L1b,L2b)

    return NewZeros

def NewZerosSubSubCell(model, L1,L2) :    
    NewZero = model.addVar(vtype='b',name="Subcell")
    L= L1+L2+[NewZero]
    with open("Midori_S_fin.esp",'r') as f :
        for line in f :
            c = 0
            for i in range(9) :
                if line[i] =='0' :
                    c+= L[i]
                elif line[i] =='1' :
                    c+= 1-L[i]
            model.addConstr(c>=1)
    
    return [NewZero]
    

def summary(model, A,B,C) :
    for a in range(2) :
        for rr in range(len(A[0])) :
            for i in range(16) :
                for j in range(8) :
                    OrList(model,[A[a][rr][i][j],B[a][rr][i][j]], C[a][rr][i][j])
  
def shuffle(state) :
    new_states = []
    for rr in range(len(state)) :
        new_states.append([state[rr][pi[i]] for i in range(16)]) 
    return new_states

def symb(model,x) :
    if round(model.cbGetSolution(x))==1 :
        return "0"
    else :
        return "*"
    
def print_row(model,A,i) :
    return "   ".join("".join(symb(model,A[ii][j]) for j in range(8))  for ii in range(i,16,4))

def Midori(r) :
    model = Model("Midori")
    # encryption proba 1 track
    is_zero_forward = [[[[model.addVar(name=f"is_zero_f_{a}_{rr}_{i}_{j}",vtype="b") for j in range(8)] for i in range(16) ] for rr in range(r)] for a in range(2)]
    is_zero_forward.append(shuffle(is_zero_forward[1]))
                       
    # [0]  : after MixColumn
    # [1] : after Subcell
    # [2] : after ShuffleCell

    model.addConstr(quicksum(is_zero_forward[0][0][i][j] for i in range(16) for j in range(8))<=8*16-1)

    # decryption proba 1 track
    is_zero_backward = [[[[model.addVar(name=f"is_zero_b_{a}_{rr}_{i}_{j}",vtype="b") for j in range(8)] for i in range(16) ] for rr in range(r)] for a in range(2)]
    is_zero_backward.append(shuffle(is_zero_backward[1]))
    model.addConstr(quicksum(is_zero_backward[2][r-1][i][j] for i in range(16) for j in range(8))<=8*16-1)


    # global summary track 
    
    is_zero_global = [[[[model.addVar(name=f"is_zero_g_{a}_{rr}_{i}_{j}",vtype="b") for j in range(8)] for i in range(16) ] for rr in range(r)] for a in range(2)]
    is_zero_global.append(shuffle(is_zero_global[1]))
    summary(model,is_zero_backward,is_zero_forward,is_zero_global)

    for i in range(16): 
        Differences_on_full_cells(model, is_zero_forward[0][0][i],i%4)
        Differences_on_full_cells(model, is_zero_backward[1][r-1][i],i%4)
    
    

    model.setParam("PoolSearchMode",2)
    model.setParam("PoolSolutions",80) 
    model.setParam("Threads",2)
    model.setParam("LazyConstraints",1)

    model._NewZerosMC = []
    model._NewZerosSC = []
    for rr in range(r) :
        # MixColumn 
        if rr<r-1 :
            for i in range(4) :
                for j in range(8) :
                    MixColumn(model, [x[j] for x in is_zero_forward[2][rr][4*i:4*i+4]], [x[j] for x in is_zero_forward[0][rr+1][4*i:4*i+4]])
                    MixColumn(model, [x[j] for x in is_zero_backward[0][rr+1][4*i:4*i+4]], [x[j] for x in is_zero_backward[2][rr][4*i:4*i+4]])
                    model._NewZerosMC+= FindNewZerosMixColumn(model, [x[j] for x in is_zero_global[2][rr][4*i:4*i+4]],[x[j] for x in is_zero_global[0][rr+1][4*i:4*i+4]])

        #SubCell
        for i in range(16) :
            SubCell(model,i%4, is_zero_forward[0][rr][i] , is_zero_forward[1][rr][i])
            SubCell(model,i%4, is_zero_backward[1][rr][i] , is_zero_backward[0][rr][i])
            # model._NewZerosSC+=FindNewZeroSubCell(model, i%4,is_zero_global[0][rr][i], is_zero_global[1][rr][i]) //  Slower and not necessary


    model.addConstr(quicksum(model._NewZerosMC+ model._NewZerosSC)>=4)


    model._is_zero_f = is_zero_forward
    model._is_zero_b = is_zero_backward
    model._is_zero_g = is_zero_global
    model._SolCount = 0

    model._valid = 0

    model.optimize(callback=my_callback)
    
 
        
        

            
def my_callback(model,where) :
    if where == GRB.Callback.MIPSOL :
        target_i = [[round(1-model.cbGetSolution(model._is_zero_f[0][0][i][j])) for j in range(8)] for i in range(16)]
        target_o = [[round(1-model.cbGetSolution(model._is_zero_b[2][-1][i][j])) for j in range(8)] for i in range(16)]
       
        r = len(model._is_zero_f[0])
        s = Midori_diff(r,target_i,target_o,model._SolCount)
       
        if s ==GRB.INFEASIBLE :
            print(f"ID n° {model._valid} --  Found an impossible differential provoked by {
                  round(sum(model.cbGetSolution(model._NewZerosMC))+sum(model.cbGetSolution(model._NewZerosSC)))} zeros")
            
            draw(model, f"MIDORI_solution_{r}_{model._valid}.tex")

            model._valid +=1
        else :
            print(f"solution {model._SolCount} is possible .. we exclude it. provoked by {round(sum(model.cbGetSolution(model._NewZerosMC))+sum(model.cbGetSolution(model._NewZerosSC)))} zeros")
            c= 0
            for i in range(16) :
                for j in range(8) :
                    if round(target_i[i][j])==1 :
                        c+= model._is_zero_f[0][0][i][j] 
                    if round(target_o[i][j])==1 :
                        c+= model._is_zero_b[2][-1][i][j] 
            model.cbLazy(c>=1)
        model._SolCount+=1

m = Midori(7)
