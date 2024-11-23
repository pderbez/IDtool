from gurobipy import *

pi = [0, 10, 5, 15, 14, 4, 11, 1, 9, 3, 12, 6, 7, 13, 2, 8]

def XOR(model,a,b,c=None) :
    if c is None :
        c = model.addVar(vtype='b')

    # c = a xor b
    # 1 + 1 = 0
    model.addConstr(2>=a+b+c)

    # 1 + 0 = 1
    model.addConstr(a+c >=b)
    model.addConstr(b+c >=a)
    # 0 + 0 = 0
    model.addConstr(a+b >=c)

    return c

def XORList(model,L,c) :
    # c = Xor(L) 
    d = XOR(model,L[0],L[1])
    for x in L[2:] :
        d = XOR(model,d,x)
    model.addConstr(d==c)
    

def MixColumn(model,L1,L2) :
    XORList(model,[L1[1],L1[2],L1[3]],L2[0])
    XORList(model,[L1[0],L1[2],L1[3]],L2[1])
    XORList(model,[L1[0],L1[1],L1[3]],L2[2])
    XORList(model,[L1[0],L1[1],L1[2]],L2[3])

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
    for x in L1 :
        model.addConstr(sum(L2)>=x)
    for x in L2 :
        model.addConstr(sum(L1)>=x)

def shuffle(state) :
    new_states = []
    for rr in range(len(state)) :
        new_states.append([state[rr][pi[i]] for i in range(16)]) 
    return new_states

def symb(x) :
    if round(x.X)==1 :
        return "1"
    else :
        return "0"
    
def print_row(A,i) :
    return "   ".join("".join(symb(A[ii][j]) for j in range(8))  for ii in range(i,16,4))

def Midori_diff(r,target_i,target_o,label="") :
    model = Model("Midori")
    model.setParam("LogToConsole",0)
    model.setParam("Threads",2)
    
    # encryption proba 1 track
    is_zero_forward = [[[[model.addVar(name=f"forward_{a}_{rr}_{i}_{j}",vtype="b") for j in range(8)] for i in range(16) ] for rr in range(r)] for a in range(2)]
    is_zero_forward.append(shuffle(is_zero_forward[1]))
                       
    # [0]  : after MixColumn
    # [1] : after Subcell
    # [2] : after ShuffleCell

    for rr in range(r) :
        # MixColumn 
        if rr<r-1 :
            for i in range(4) :
                for j in range(8) :
                    MixColumn(model, [x[j] for x in is_zero_forward[2][rr][4*i:4*i+4]], [x[j] for x in is_zero_forward[0][rr+1][4*i:4*i+4]])
                    MixColumn(model, [x[j] for x in is_zero_forward[0][rr+1][4*i:4*i+4]], [x[j] for x in is_zero_forward[2][rr][4*i:4*i+4]])

                   
        #SubCell
        for i in range(16) :
            SubCell(model,i%4, is_zero_forward[0][rr][i] , is_zero_forward[1][rr][i])
          


    for i in range(16) :
        for j in range(8) :
            model.addConstr(is_zero_forward[0][0][i][j]==target_i[i][j])
            model.addConstr(is_zero_forward[2][r-1][i][j]==target_o[i][j])
 
    model.optimize()
    
    return model.Status


if __name__ == "__main__" :

    target_i = [[0 for _ in range(8)] for _ in range(16)]
    target_o = [[0 for _ in range(8)] for _ in range(16)]
    Midori_diff(7, target_i,target_o)

    target_o[0][0]=1
    Midori_diff(7, target_i,target_o)



    print("-----------------")
    target_i = [[0 for _ in range(8)] for _ in range(16)]
    for j in [1,3,4,6] :
        target_i[8][j] = 1
    for j in range(8) :
        target_i[12][j]=1

    
    target_o = [[0 for _ in range(8)] for _ in range(16)]

    for j in [1,3,4,6] :
        target_o[15][j] = 1


    s= Midori_diff(7, target_i,target_o,label="verif")
    print( s==GRB.INFEASIBLE)
