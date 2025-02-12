COLOR_FORWARD_DISTINGUISHER = "WildStrawberry!80"
COLOR_BACKWARD_DISTINGUISHER = "NavyBlue!80"
COLOR_COL_NEW_ZEROS = "ForestGreen!90"
COLOR_INVOLVED_CELLS_F = "yellow!50"
COLOR_INVOLVED_CELLS_B = "green!50"
COLOR_VALUE_NEEDED_F = "ForestGreen!60"



def drawGrid(x,y, file_name, UpperTrail, LowerTrail, NewZeros) :
    w = min(len(UpperTrail)//2, 32) *1.0/ len(UpperTrail)
    with open(file_name, "a") as f:
        for j in range(len(UpperTrail)):
            if UpperTrail[j] == 1:
                f.write(f"\\draw[fill={COLOR_FORWARD_DISTINGUISHER},draw opacity=0] ({x+j*w},{y}) -- ++(0,1) --++({w},0) --  cycle ;\n")
            if LowerTrail[j] == 1 :
                f.write(f"\\draw[fill={COLOR_BACKWARD_DISTINGUISHER},draw opacity=0] ({x+j*w},{y}) -- ++({w},0) --++(0,1) --  cycle ;\n")
    
        f.write(f"\\draw ({x},{y}) rectangle  ++ ({len(UpperTrail)*w},1); \n")

        if NewZeros is not None :
            for j in range(len(UpperTrail)) :
                if NewZeros[j]!=0 :
                    f.write(f"\\draw[draw={COLOR_COL_NEW_ZEROS}, ultra thick]({x+j*w},{y-0.1}) rectangle  ++ ({w},1.2); \n")

def NeededGrid(x,y, file_name, neededTrail, text="") :
    w = min(len(neededTrail)//2, 32) *1.0/ len(neededTrail)
    with open(file_name, "a") as f:
        for j in range(len(neededTrail)):
            if neededTrail[j] >0.5:
                f.write(f"\\draw[draw={COLOR_VALUE_NEEDED_F},ultra thick] ({x+j*w},{y+1} )--++({w},-1);\n")
            f.write(f"\\draw ({x+j*w},{y}) rectangle  ++ ({w},1); \n")
        
        f.write(f"\\node at ({x},{y+1.2}) "+"{$" + text +"$};\n")

def drawFeistel(y, w,file_name ) :
    with open(file_name, "a") as f:
        f.write(f"\\draw[->]({w//2},{y}) -- ++(0,-1) -- ++(5,0) node[midway, draw, fill =white] "+"{ S } ;\n")
        f.write(f"\\node[inner sep=0] (X{y}) at  ({w+10+w//2},{y-1}) "+ "{ $ \\bigoplus $} ;\n")
        f.write(f"\\draw[->]({w+10+w//2},{y}) -- (X{y}) ;\n")
        f.write(f"\\draw[->] (X{y}) -- ++ (0,-1) -- ({w//2},{y-2.5}) -- ++(0,-0.5);\n")
        f.write(f"\\draw[->]({w//2},{y-1}) -- ++(0,-1) -- ({w+10+w//2},{y-2.5})- -++(0,-0.5);\n")
        f.write(f"\\draw[->]({w+w//2+5},{y-1}) -- (X{y}) ;\n")


def drawFilter(x,y, file_name, Filters) :
    w = min(len(Filters)//2, 32) *1.0/ len(Filters)
    with open(file_name, "a") as f:
        for j in range(len(Filters)):
            if Filters[j] == 1:
                f.write(f"\\draw[draw=yellow, thick] ({x+j*w},{y}) rectangle  ++ ({w},1); \n")


def draw(model, algo,comp):

    rD = len(model._summary)-1

    rB = len(model._is_zero_forward)-len(model._summary)
    rF = len(model._is_zero_backward)-len(model._summary)
    n = len(model._summary[0][0])
    w = min(n//2, 32)

    file_name = f"sol/{algo}-{2*n}-{model._keysize}_({rB},{rD},{rF})_sol{model._valid}_{round(comp,2)}.tex"

  
    Backward_rounds=  [[[round(model.cbGetSolution(model._is_zero_forward[r][a][j]))  for j in range(n)]  for a in range(3)] for r in range(rB)]
    Forward_rounds =  [[[round(model.cbGetSolution(model._is_zero_backward[r][a][j]))  for j in range(n)]  for a in range(3)] for r in range(rD,rD+rF+1)]

    UpperTrail = [[[round(model.cbGetSolution(model._is_zero_forward[rB+r][a][j]))  for j in range(n)]  for a in range(3)] for r in range(rD+1)]
    LowerTrail = [[[round(model.cbGetSolution(model._is_zero_backward[r][a][j])) for j in range(n)]  for a in range(3)] for r in range(rD+1)]

    Backward_NeededKR = [[[round(model.cbGetSolution(model._value_needed_backward[r][a][j]))  for j in range(n)]  for a in range(3)] for r in range(rB)]
    KR = [[round(model.cbGetSolution(model._key_recovery_forward[r][j]))  for j in range(n)]  for r in range(rB)]

    Forward_NeededKR = [[[round(model.cbGetSolution(model._value_needed_forward[r][a][j]))  for j in range(n)]  for a in range(3)] for r in range(rF)]
    BKR = [[round(model.cbGetSolution(model._key_recovery_backward[r][j]))  for j in range(n)]  for r in range(rF)]
    

    NewZeros = [round(model.cbGetSolution(x)) for x in model._NewZeros]

    # Filter_B = [[round(model.cbGetSolution(x[j]))  for j in range(n) ] for x in model._XORCancellation_B]
    # Filter_F = [[round(model.cbGetSolution(x[j])) for j in range(n) ] for x in model._XORCancellation_F]
   

    # WXY = [[[round(model.cbGetSolution(x)) for x in a] for a in L ] for L in model._store] 
    # for L in WXY :
    #     a,b = [[i for i in range(16) if x[i]==1] for x in L]
    #     print(a,b, set([(x+8)%16 for x in a]+[(x+1)%16 for x in b]))

    # # for r in range(rF) :
    # #     print([model.cbGetSolution(model._key_recovery_backward[r][j]) for j in range(n)] , BKR[r])
    

    with open(file_name, "w") as f:
        f.write(
            "\\documentclass{standalone}\n\\usepackage[dvipsnames]{xcolor}\n\\usepackage{tikz}\n\\usetikzlibrary{arrows}\n\\usetikzlibrary{calc}\n\\usetikzlibrary{positioning}\n")
        f.write("\\begin{document}\n")
        f.write("\\begin{tikzpicture}\n")


    for r in range(len(Backward_rounds)) :
        z= 4*len(Backward_rounds) - 4*r
        drawGrid(0, z, file_name,Backward_rounds[r][0], [0]*n,   None)
        drawGrid(w+10, z,file_name, Backward_rounds[r][1], [0]*n, None )
        drawGrid(w/2 + 5 ,z-1.5,file_name, Backward_rounds[r][2], [0]*n, None)      

        NeededGrid(0,z,file_name, Backward_NeededKR[r][0])
        NeededGrid(w+10,z,file_name, Backward_NeededKR[r][1])
        NeededGrid(w/2+5,z-1.5, file_name, Backward_NeededKR[r][2])
 
            
        drawFeistel(z, w , file_name)
        
        if r>0 :
            NeededGrid(-8, z-2, file_name,KR[r] ,text=f"K^e_{r}" )
            # drawFilter(0,z, file_name, Filter_B[r-1])
           

    
    for r in range(len(UpperTrail)) :
        z = -4*r
        drawGrid(0,z, file_name, UpperTrail[r][0], LowerTrail[r][0],  NewZeros[n*(r-1):n*(r)] if r>0  else None)
        drawGrid(w+10, z, file_name, UpperTrail[r][1], LowerTrail[r][1],  NewZeros[n*r:n*(r+1)] if r+1<len(UpperTrail)  else None )
        if r+1<len(UpperTrail) :
            drawGrid(w/2 + 5 , z-1.5,file_name, UpperTrail[r][2], LowerTrail[r][2], NewZeros[n*r:n*(r+1)])      
            drawFeistel(z, w , file_name)


    # drawFilter(0,0, file_name, Filter_B[-1])
    
    for r in range(len(Forward_rounds)) :
        z = -4*(len(UpperTrail)-1)-4*r
        drawGrid(0, z, file_name,[0]*n, Forward_rounds[r][0],    None)
        drawGrid(w+10, z, file_name, [0]*n, Forward_rounds[r][1], None )
        if r+1<len(Forward_rounds) :
            drawFeistel(z, w , file_name)
            drawGrid(w/2 + 5 ,z-1.5,file_name, [0]*n, Forward_rounds[r][2],  None)      

            if r+2<len(Forward_rounds) :
                NeededGrid(-8, z-2, file_name,BKR[r] ,text="K^e_{"+str(r+ len(UpperTrail)+len(Backward_rounds)-1)+"}" )
            
            NeededGrid(0,z,file_name, Forward_NeededKR[r][0])
            NeededGrid(w+10,z,file_name, Forward_NeededKR[r][1])
            NeededGrid(w/2+5,z-1.5, file_name, Forward_NeededKR[r][2])

        # if r+2 < len(Forward_rounds):
        #     drawFilter(w+10,z, file_name, Filter_F[r])
            
        



    with open(file_name, "a") as f:
        f.write('\\end{tikzpicture}\n\\end{document}\n')

 

