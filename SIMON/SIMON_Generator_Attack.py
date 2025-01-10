import gurobipy as gp
import SIMON_Validator 
from draw_SIMON import draw


def getSummaryBit(M, a, b):
    # 0+0 =0 , *+0 = 0 , *+* = *
    # Non 0,0,*
    # Non 0,_ 1
    s = M.addVar(vtype="b")
    M.addConstr(2*s <= a+b)

    M.addConstr(a+b <= 1+s)
    return s


def getSummary(M, X, Y):
    n = len(X[0])
    return [[getSummaryBit(M, X[j][i], Y[j][i]) for i in range(n)] for j in range(3)]


def AND(M, a, b, c=None):
    # 0 x 0 = 0
    # * x * = *
    # * x 0 = *
    if c is None:
        c = M.addVar(vtype="b")
    M.addConstr(a+b >= c)
    M.addConstr(2*c >= a+b)
 
    return c


def XOR(M, a, b, s=None):
    if s is None:
        s = M.addVar(vtype="b")

    M.addConstr(a +b <= 2*s)
    M.addConstr(a+b >= s)

    return s

def XORList(M, L, s=None): 
    if s is None:
        s = M.addVar(vtype="b")

    M.addConstr(sum(L) <= len(L)*s)
    M.addConstr(sum(L) >= s)

    return s


def XORState(M, X, Y, Z=None):
    if Z is None:
        Z = [M.addVar(vtype="b") for _ in range(len(X))]
    for i in range(len(X)):
        XOR(M, X[i], Y[i], Z[i])
    return Z

def XORStateList(M, X, Z=None):
    
    if Z is None:
        Z = [M.addVar(vtype="b") for _ in range(len(X[0]))] 
    
    for i in range(len(X[0])):
        XORList(M, [a[i] for a in X] ,  Z[i])
    return Z


def ANDState(M, X, Y, Z=None):
    if Z is None:
        Z = [M.addVar(vtype="b") for _ in range(len(X))]
    for i in range(len(X)):
        AND(M, X[i], Y[i], Z[i])
    return Z

def Cmp(M,x,y,z) :
    # if z=1 then t=1
    #else 
      #  t=y

    t= M.addVar(vtype="b")
    M.addConstr(1-z+t>=1)
    M.addConstr(z+1-y+t>=1)
    M.addConstr(z+y+1-t>=1)
    return t


def CmpState(M,X,Y,Z): 
    return [Cmp(M,X[i],Y[i],Z[i]) for i in range(len(X))]


def Rotate(state,r) :
    return state[r:]+state[:r]

def FeistelFunction(M, state):
    return XORState(M, Rotate(state,2), ANDState(M, Rotate(state,8), Rotate(state,1)))





def FindNewZerosXOR(M, a, b, c):  # c=a XOR b
    NewZero = M.addVar(vtype="b")
    # b = 0 => No new Zero
    M.addConstr(b >= NewZero)
    # b= 1  and a=c=0 => New Zero
    M.addConstr(a+c + NewZero >= b)
    # b=1 and a=1 or c==1 => No NewZero
    M.addConstr(1 >= a+NewZero)
    M.addConstr(1 >= c+NewZero)

    return NewZero


def FindNewZeros(M,R, tmp, LL):
    n = len(R)
    return [FindNewZerosXOR(M, R[i],tmp[i],LL[i]) for i in range(n)]


def my_callback(model, where):

    if where == gp.GRB.Callback.MIPSOL:

        model._solCount += 1
        n = len(model._summary[0][0])

        target_i = [[round(model.cbGetSolution(model._summary[0][0][i]))
                    for i in range(n)], [round(model.cbGetSolution(model._summary[0][1][i])) for i in range(n)]]
        target_o = [[round(model.cbGetSolution(model._summary[-1][0][i]))
                    for i in range(n)], [round(model.cbGetSolution(model._summary[-1][1][i])) for i in range(n)]]

        rD = len(model._summary)

    
        s = SIMON_Validator.is_differential_possible(
            target_i, target_o, rD-1, n)
     
        if s == gp.GRB.INFEASIBLE:
            nb_one = sum(target_i[0])+sum(target_i[1])+sum(target_o[0])+sum(target_o[1])
            print(f"Found an impossible differential provoked by {
                  round(sum(model.cbGetSolution(model._NewZeros)))} zeros. It has {nb_one} active bits")
            print("ID:", "".join([str(x) for x in target_i[0]]) + " "+"".join([str(x) for x in target_i[1]]),
                  " -/->  "+"".join([str(x) for x in target_o[0]]) + " " + "".join([str(x) for x in target_o[1]]))

            draw(model, "SIMON")

            model._valid += 1
            print(model.cbGet(gp.GRB.Callback.RUNTIME) )

        else:
            if model._solCount %50 ==0 :
                print(f"solution {model._solCount} is possible .. we exclude it")

            c = 0
            for i in range(len(target_i[0])):
                if round(target_i[0][i]) == 1:
                    c += 1-model._summary[0][0][i]
                # else:
                #     c += model._summary[0][0][i]
                if round(target_o[0][i]) == 1:
                    c += 1-model._summary[-1][0][i]
                # else:
                #     c += model._summary[-1][0][i]
                if round(target_i[1][i]) == 1:
                    c += 1-model._summary[0][1][i]
                # else:
                #     c += model._summary[0][1][i]
                if round(target_o[1][i]) == 1:
                    c += 1-model._summary[-1][1][i]
                # else:
                #     c += model._summary[-1][1][i]

            model.cbLazy(c >= 1)

def newState(M,n) :
    return [M.addVar(vtype='b') for _ in range(n)]

def Combine(M,VX, VY, S, a,b ) :
    n = len(VX)
    Sa = Rotate(S,a)
    Sb = Rotate(S,b)

    WX = newState(M,n)
    WY = newState(M,n)
    for i in range(n): 
  


        M.addConstr(1-Sa[i] + WX[i] >= VX[i])
        M.addConstr(1-Sa[i] + VX[i] >= WX[i])

        M.addConstr(1-Sb[i] + WX[i] >= VX[i])
        M.addConstr(1-Sb[i] + VX[i] >= WX[i])


        M.addConstr(1-Sb[i] + WY[i] >= VY[i])
        M.addConstr(1-Sb[i] + VY[i] >= WY[i])

        M.addConstr(1-Sa[i] + WY[i] >= VY[i])
        M.addConstr(1-Sa[i] + VY[i] >= WY[i])

        # M.addConstr(1-Sb[i] + VY[i] >= WY[i])
        # M.addConstr(1-Sb[i] + WY[i] >= VY[i])

        M.addConstr(Sa[i]+Sb[i] + 1-VX[i]+1-VY[i]+ WX[i] +WY[i]>=1)
        M.addConstr(Sa[i]+Sb[i] + VX[i]+ 1-VY[i] +WY[i]>=1)
        M.addConstr(Sa[i]+Sb[i] + VY[i]+ 1-VX[i] +WX[i]>=1)
        M.addConstr(Sa[i]+Sb[i] + VX[i]+ VY[i] + 1-WX[i]>=1)
        M.addConstr(Sa[i]+Sb[i] + VX[i]+ VY[i] + 1-WY[i]>=1)


    K = XORState(M,Rotate(WX,-a), Rotate(WY,-b))

    M._store.append([WX,WY])

    return K


def find_impossible_differential(rB,rD,rF, n):
    M = gp.Model()
    M.setParam("LazyConstraints", 1)

    M._is_zero_forward = []
    M._is_zero_backward = []

    M._NewZeros = []

    M._solCount = 0
    M._valid = 0

    M._store=[]

    Lf = newState(M,n)
    Lb = newState(M,n)
    M._is_zero_forward = [[Lf, newState(M,n), FeistelFunction(M, Lf)] ] +  [[newState(M,n), None ,None ] for  _ in range(rB+rD)]
    M._is_zero_backward = [[Lb, newState(M,n), FeistelFunction(M,Lb)]] +  [[newState(M,n), None ,None ] for  _ in range(rF+rD)]

    M._value_needed_backward = [[newState(M,n), newState(M,n), None]] +  [[newState(M,n), None ,None ] for  _ in range(rB)]
    M._value_needed_forward =  [[newState(M,n), newState(M,n), None]] +  [[ None, newState(M,n),None ] for  _ in range(rF)]

    M._key_recovery_forward = []
    M._key_recovery_backward = []

    # Key recovery (backward propagation)
    for r in range(rB):
        XORState(M, M._is_zero_forward[r+1][0],
                 M._is_zero_forward[r][2], M._is_zero_forward[r][1])
        
        M._is_zero_forward[r+1][1] =  M._is_zero_forward[r][0]
        M._is_zero_forward[r+1][2] = FeistelFunction(M, M._is_zero_forward[r+1][0])

        M._value_needed_backward[r][2] = M._value_needed_backward[r+1][0]
        M._value_needed_backward[r][1] = M._value_needed_backward[r+1][0]

    M._value_needed_backward[rB][1] = newState(M,n) 

    for r in range(rB) : 
        ValueNeededInX = CmpState(M,Rotate(M._is_zero_forward[r][0],8), Rotate(M._is_zero_forward[r][0],1), M._value_needed_backward[r][2]  )
        ValueNeededInY = CmpState(M,Rotate(M._is_zero_forward[r][0],1), Rotate(M._is_zero_forward[r][0],8),  M._value_needed_backward[r][2] )

        M._key_recovery_forward.append(Combine(M, ValueNeededInX, ValueNeededInY, M._is_zero_forward[r][0], 8,1))
        #M._key_recovery_forward.append(XORState(M, Rotate(ValueNeededInX,-8), Rotate(ValueNeededInY,-1)))
   
        XORStateList(M, [M._value_needed_backward[r+1][1] , Rotate(M._value_needed_backward[r][2],-2),  M._key_recovery_forward[-1]] , M._value_needed_backward[r][0])
       

    M.addConstrs(M._value_needed_backward[rB][0][i] == 0 for i in range(n))
    M.addConstrs(M._value_needed_backward[rB][1][i] == 0 for i in range(n))

    M.addConstrs(M._is_zero_forward[rB][0][i] == 0 for i in range(n))
    for i in range(n) :
        if i in  [6] : #[1,3,10] :
            M.addConstr(M._is_zero_forward[rB][1][i]==1)
        else :
            M.addConstr(M._is_zero_forward[rB][1][i]==0)


    # Distinguisher
    for r in range(rD):

        XORState(M, M._is_zero_forward[rB+r][1], M._is_zero_forward[rB+r][2], M._is_zero_forward[rB+r+1][0])

        XORState(M, M._is_zero_backward[r+1][0],
                 M._is_zero_backward[r][2], M._is_zero_backward[r][1])

        
        M._is_zero_forward[rB+r+1][1] =  M._is_zero_forward[rB+r][0]
        M._is_zero_backward[r+1][1] =  M._is_zero_backward[r][0]

        M._is_zero_forward[rB+r+1][2] =  FeistelFunction(M,M._is_zero_forward[rB+r+1][0])
        M._is_zero_backward[r+1][2] = FeistelFunction(M, M._is_zero_backward[r+1][0])



    M._summary= [getSummary(M, M._is_zero_forward[rB+r], M._is_zero_backward[r]) for r in range(rD+1)]
    
    for r in range(rD):
        M._NewZeros += FindNewZeros(M, M._summary[r][1], M._summary[r][2], M._summary[r+1][0])

    M.addConstr(gp.quicksum(M._NewZeros)>=1)

    # Key recovery (forward propagation )
    for r in range(rD, rD+rF):
        XORState(M, M._is_zero_backward[r][1],
                 M._is_zero_backward[r][2], M._is_zero_backward[r+1][0])
        M._is_zero_backward[r+1][1] =  M._is_zero_backward[r][0]
        M._is_zero_backward[r+1][2] = FeistelFunction(M, M._is_zero_backward[r+1][0])

    for r in range(rF) :
        M._value_needed_forward[r][2] = M._value_needed_forward[r][1]
        M._value_needed_forward[r+1][0] = M._value_needed_forward[r][1]

    M._value_needed_forward[-1][1] = newState(M,n) 

    for r in range(rF) : 
        ValueNeededInX = CmpState(M,Rotate(M._is_zero_backward[rD+r+1][1],8), Rotate(M._is_zero_backward[rD+r+1][1],1), M._value_needed_forward[r][2]  )
        ValueNeededInY = CmpState(M,Rotate(M._is_zero_backward[rD+r+1][1],1), Rotate(M._is_zero_backward[rD+r+1][1],8),  M._value_needed_forward[r][2] )
        #M._key_recovery_backward.append(XORState(M, Rotate(ValueNeededInX,-8), Rotate(ValueNeededInY,-1)))
        M._key_recovery_backward.append(Combine(M, ValueNeededInX, ValueNeededInY, M._is_zero_backward[rD+r+1][1], 8,1))
   
        XORStateList(M, [M._value_needed_forward[r][0] , Rotate(M._value_needed_forward[r][2],-2),  M._key_recovery_backward[-1]] , M._value_needed_forward[r+1][1])
       


    M.addConstrs(M._value_needed_forward[0][0][i] == 0 for i in range(n))
    M.addConstrs(M._value_needed_forward[0][1][i] == 0 for i in range(n))


    M.addConstrs(M._summary[-1][1][i] == 0 for i in range(n))
    for i in range(n) :
        if i in [15] :
            M.addConstr(M._summary[-1][0][i]==1)
        else :
            M.addConstr(M._summary[-1][0][i]==0)

   
    # Mode 1 : maximize number of zeros 
    
    # M.setObjective(-gp.quicksum(M._NewZeros))

    # Mode 2 : Maximize number of active bits  (with heuristics Number of zeros >=3)
    M.addConstr(gp.quicksum(M._NewZeros) >= 3)
    # M.setObjective(-(gp.quicksum(M._is_zero_forward[0][0]) + gp.quicksum(M._is_zero_forward[0][1]) +
                #    gp.quicksum(M._is_zero_backward[-1][0]) +  gp.quicksum(M._is_zero_backward[-1][1])))


    # M.addConstr(M._summary[0][0][0] + M._summary[0][1][0]>=1)

    M.setObjective(gp.quicksum(gp.quicksum(x) for x in M._key_recovery_forward[1:])+ gp.quicksum(gp.quicksum(x) for x in M._key_recovery_backward[:rF-1]))

    M.optimize(my_callback)
    print(M.objVal)

    print(f"============= {rD} rounds == SIMON-{2*n} ==  Explored {
          M._solCount} solutions and found {M._valid} ID in { round(M.Runtime,2)} seconds ==========")


# find_impossible_differential(3,11,5, 16)
find_impossible_differential(4,11,5,16)

# find_impossible_differential(12, 24)

# find_impossible_differential(5,13,5, 32)


# find_impossible_differential(16, 48)

# find_impossible_differential(4,19,4, 64)

# find_impossible_differential(12, 16)
# find_impossible_differential(13, 24)
# find_impossible_differential(14, 32)
# find_impossible_differential(17, 48)
# find_impossible_differential(20, 64)
