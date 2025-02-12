import gurobipy as gp
import SIMON_Validator 
from draw_SIMON import draw

gp.setParam("LogToConsole", 0)

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
            
            # print("ID:", "".join([str(x) for x in target_i[0]]) + " "+"".join([str(x) for x in target_i[1]]),
            #       " -/->  "+"".join([str(x) for x in target_o[0]]) + " " + "".join([str(x) for x in target_o[1]]))
            print(f"Found an impossible differential provoked by {
                  round(sum(model.cbGetSolution(model._NewZeros)))} zeros. It has {nb_one} active bits" ,model.cbGet(gp.GRB.Callback.RUNTIME))
            draw(model, "SIMON", model.cbGet(gp.GRB.Callback.MIPSOL_OBJ))

            model._valid += 1
            # print(model.cbGet(gp.GRB.Callback.RUNTIME))

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

# def Cancel(M, A,B, C, out) :
    
#     for i in range(len(out)) :
#         # if A = B= 1 and C=0 then out =1
#         M.addConstr(1-A[i]+1-B[i]+C[i] + out[i]>=1)

#         # if C=1 then out = 0
#         M.addConstr(1-C[i]>=out[i])


def find_impossible_differential(rB,rD,rF, n, keysize):
    M = gp.Model()
    M.setParam("LazyConstraints", 1)
    M.setParam("LogToConsole",1)
    M.setParam("TimeLimit", 15*60)

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

    # M._XORCancellation_B = [ newState(M,n) for _ in range(rB)]
    # M._XORCancellation_F =[ newState(M,n) for _ in range(rF)]

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

        # Cancel(M,ANDState(M,Rotate(M._is_zero_forward[r][0], 8), Rotate(M._is_zero_forward[r][0],1)),  Rotate(M._is_zero_forward[r][0],2), M._is_zero_forward[r][2], M._XORCancellation_B[r][0] )      
        # Cancel(M,M._is_zero_forward[r][1], M._is_zero_forward[r][2], M._is_zero_forward[r+1][0], M._XORCancellation_B[r])

    M.addConstrs(M._value_needed_backward[rB][0][i] == 0 for i in range(n))
    M.addConstrs(M._value_needed_backward[rB][1][i] == 0 for i in range(n))

  


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

        # Cancel(M,M._is_zero_backward[rD+r][2], M._is_zero_backward[rD+r+1][0], M._is_zero_backward[rD+r][1], M._XORCancellation_F[r])


    M.addConstrs(M._value_needed_forward[0][0][i] == 0 for i in range(n))
    M.addConstrs(M._value_needed_forward[0][1][i] == 0 for i in range(n))


    M.addConstr(gp.quicksum(M._NewZeros) >= 3)
    M.addConstr(M._summary[0][0][0] + M._summary[0][1][0]>=1)

    # Complexity estimation
    DX = gp.quicksum(M._summary[0][0]+M._summary[0][1])-1
    DY = gp.quicksum(M._summary[-1][0]+M._summary[-1][1])-1

    Din = gp.quicksum(M._is_zero_forward[0][0]+M._is_zero_forward[0][1])-1
    Dout = gp.quicksum(M._is_zero_backward[-1][0]+M._is_zero_backward[-1][1])-1

    cin = Din -DX #gp.quicksum(gp.quicksum(X) for X in M._XORCancellation_B) - rB
    cout = Dout -DY # gp.quicksum(gp.quicksum(X) for X in M._XORCancellation_F) -rF

    M.addConstr(Dout>=Din)

    KinKout = gp.quicksum(gp.quicksum(x) for x in M._key_recovery_forward[1:])+ gp.quicksum(gp.quicksum(x) for x in M._key_recovery_backward[:rF-1])

    # formula = max(cin+cout - 0.5  , |kin u kout| - 0.5, cin + cout - 0.5 +  n + 1 - |Din| - |Dout|, ( n + 1 - 0.5 - DY +  cin )/2)
    Term1, Term2, Term3, Term4, complexity,  = [M.addVar(vtype=gp.GRB.CONTINUOUS) for _ in range(5)]
    M.addConstr(Term1 == cin+cout - 0.53 )
    M.addConstr(Term2 == KinKout - 0.53)
    M.addConstr(Term3 == cin+cout - 0.53+2*n+1 - Din-Dout )
    M.addConstr(Term4 == (-0.53+2*n+1-DY +cin)/2)  
    M.addConstr(complexity >= Term1)
    M.addConstr(complexity >= Term2)
    M.addConstr(complexity >= Term3)
    M.addConstr(complexity >= Term4)

    M.setObjective(complexity)

    # The data complexity is over estimated.  we tolerate a small margin to correct this manually later on
    M.addConstr(Term4<= 2.2*n) 
    M.addConstr(Term3 <=2.2*n) 

    M.addConstr(complexity<= keysize)

    vCin, vCout, vDX, vDY  = [M.addVar(vtype=gp.GRB.CONTINUOUS) for  _ in range(4)]

    M.addConstr(vCin == cin )
    M.addConstr(vCout == cout)
    M.addConstr(vDX == DX)
    M.addConstr(vDY == DY)
    M._keysize=keysize

    M.optimize(my_callback)

    try : 
        print(f"cin = {vCin.X}; cout= {vCout.X}, dX = {vDX.X}, DY = {vDY.X}")

        print(f"cin+cout - 0.5  = {Term1.X}, |kin u kout| - 0.5 = {Term2.X}, cin + cout - 0.5 +  n + 1 - |Din| - |Dout|  ={Term3.X}, ( n + 1 - 0.5 - DY +  cin )/2 = {Term4.X}" )
        print(M.objVal)

        
        
    except :
        pass

    print(f"============= {(rB,rD,rF)} rounds == SIMON-{2*n}-{keysize} ==  Explored {
            M._solCount} solutions and found {M._valid} ID in { round(M.Runtime,2)} seconds ==========")


# # # 32	64	3	11	5
# find_impossible_differential(3,11,5, 16, 64)

# # # 32	64	4	11	5
# find_impossible_differential(4,11,5, 16, 64)

# # # 48	72	4	12	4
# find_impossible_differential(4,12,4, 24, 72)

# # 48	96	4	12	5
# find_impossible_differential(4,12,5, 48, 96) 

# # 64	96	3	13	5
# find_impossible_differential(3,13,5, 32, 96)

# # 64	96	4	13	5
# find_impossible_differential(4,13,5, 32, 96)

# 64	128	4	13	5
# find_impossible_differential(4,13,5, 32, 128)

# # 64	128	5	13	5
find_impossible_differential(5,13,5, 32, 128)

# # 96	96	4	16	4
# find_impossible_differential(4,16,4, 48, 96)

# # 96	144	4	16	5
# find_impossible_differential(4,16,5, 48, 144) 

# # 128	128	4	19	4
# find_impossible_differential(4,19,4, 64, 128)

# 128	128	4	19	5
# find_impossible_differential(4,19,5, 64, 128)

# # 128	192	5	19	5
# find_impossible_differential(5,19,5, 64, 192)

# # 128	192	5	19	6
# find_impossible_differential(5,19,6, 64, 192)

# 128	256	5	19	6
# find_impossible_differential(5,19,6, 64, 256)

# 128	256	6	19	6
# find_impossible_differential(6,19,6, 64, 256)
