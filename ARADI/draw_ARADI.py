COLOR_FORWARD_DISTINGUISHER = "WildStrawberry!80"
COLOR_BACKWARD_DISTINGUISHER = "NavyBlue!80"
COLOR_COL_NEW_ZEROS = [f"Peach",  "Plum","Aquamarine","BrickRed","PineGreen"]
COLOR_INVOLVED_CELLS_F = "yellow!50"
COLOR_INVOLVED_CELLS_B = "green!50"
COLOR_VALUE_NEEDED_F = "ForestGreen!60"

from ARADI import M

w=1/2
l=2
global c
c=0

def drawGrid(x,y, file_name, UpperTrail, LowerTrail, NewZeros, index=0) :
    with open(file_name, "a") as f:
        for j in range(len(UpperTrail)):
            if UpperTrail[j] == 1:
                f.write(f"\\draw[fill={COLOR_FORWARD_DISTINGUISHER},draw opacity=0] ({x+j*w},{y}) -- ++(0,1) --++({w},0) --  cycle ;\n")
            if LowerTrail[j] == 1 :
                f.write(f"\\draw[fill={COLOR_BACKWARD_DISTINGUISHER},draw opacity=0] ({x+j*w},{y}) -- ++({w},0) --++(0,1) --  cycle ;\n")
    
        f.write(f"\\draw ({x},{y}) rectangle  ++ ({len(UpperTrail)*w},1); \n")

        global c
        if NewZeros is not None :
            for j in range(len(UpperTrail)) :
                if NewZeros[0][j]!=0 : 
                    f.write(f"\\draw[draw={COLOR_COL_NEW_ZEROS[c]}, ultra thick]({x+j*w},{y-0.05*c}) rectangle  ++ ({w},1+ {2*0.05*c}); \n")
                    for k in range(32) :
                        if M[index%4][j,k] ==1 :
                            f.write(f"\\draw[draw={COLOR_COL_NEW_ZEROS[c]}, ultra thick]({x+k*w},{y+l-0.05*c}) rectangle  ++ ({w},1+ {2*0.05*c}); \n")
                  
                    c+=1

                if NewZeros[1][j]!=0 : 
                    f.write(f"\\draw[draw={COLOR_COL_NEW_ZEROS[c]}, ultra thick]({x+j*w},{y+l-0.05*c}) rectangle  ++ ({w},1+ {2*0.05*c}); \n")
                    for k in range(32) :
                        if M[index%4][j,k] ==1 :
                            f.write(f"\\draw[draw={COLOR_COL_NEW_ZEROS[c]}, ultra thick]({x+k*w},{y-0.05*c}) rectangle  ++ ({w},1+ {2*0.05*c}); \n")
                   
                    c+=1
               
def NeededGrid(x,y, file_name, neededTrail) :
    with open(file_name, "a") as f:
        for j in range(len(neededTrail)):
            if neededTrail[j] >0.5:
                f.write(f"\\draw[draw={COLOR_VALUE_NEEDED_F},ultra thick] ({x+j*w},{y+1} )--++({w},-1);\n")
            f.write(f"\\draw ({x+j*w},{y}) rectangle  ++ ({w},1); \n")

def drawTransition(z, file_name, i) :
    with open(file_name, "a") as f: 
        f.write(f"\\draw[->, thick] ({w*16},{z}) -- ++ (0,{-0.2}) node[below ] (A) "+"{$\\bigoplus $} ;\n")
        f.write(f"\\node[right = 2mm of A]"+ "{$K_{"+str(i)+"}$} ; \n")
        f.write(f"\\draw[->, thick] (A) -- ({w*16}, {z-(l-1)}) node[midway, right = 2mm] "+ "{$S$, $\Lambda_{"+str(i%4)+"}$} ;\n")
    


def draw(model, comp):

    rD = len(model._summary)-1

    rB = len(model._is_zero_forward)-len(model._summary)
    rF = len(model._is_zero_backward)-len(model._summary)

    n = len(model._summary[0])

    file_name = f"ARADI_offset{model._offset}_({rB},{rD},{rF})_sol{model._valid}_{round(comp,2)}.tex"

  
    Backward_rounds=  [[round(model.cbGetSolution(model._is_zero_forward[r][j]))  for j in range(n)]   for r in range(rB)]
    Forward_rounds =  [[round(model.cbGetSolution(model._is_zero_backward[r][j]))  for j in range(n)]  for r in range(rD,rD+rF+1)]

    UpperTrail = [[round(model.cbGetSolution(model._is_zero_forward[rB+r][j]))  for j in range(n)]  for r in range(rD+1)]
    LowerTrail = [[round(model.cbGetSolution(model._is_zero_backward[r][j])) for j in range(n)]  for r in range(rD+1)]

    Backward_NeededKR = [[round(model.cbGetSolution(model._value_needed_backward[r][j]))  for j in range(n)]  for r in range(rB)]
    Forward_NeededKR = [[round(model.cbGetSolution(model._value_needed_forward[r][j]))  for j in range(n)]  for r in range(rF+1)]    

    NewZeros0 = [round(model.cbGetSolution(x)) for x in model._NewZeros[0]]
    NewZeros1 = [round(model.cbGetSolution(x)) for x in model._NewZeros[1]]

    with open(file_name, "w") as f:
        f.write(
            "\\documentclass{standalone}\n\\usepackage[dvipsnames]{xcolor}\n\\usepackage{tikz}\n\\usetikzlibrary{arrows}\n\\usetikzlibrary{calc}\n\\usetikzlibrary{positioning}\n")
        f.write("\\begin{document}\n")
        f.write("\\begin{tikzpicture}[every node/.style={inner sep=0,outer sep=0}]\n")


    for r in range(len(Backward_rounds)) :
        z= l*len(Backward_rounds) - l*r
        drawGrid(0, z, file_name,Backward_rounds[r], [0]*n,   None)
        NeededGrid(0,z,file_name, Backward_NeededKR[r]) 
        drawTransition(z, file_name,model._offset+r)         

    
    for r in range(len(UpperTrail)) :
        z = -l*r
        drawGrid(0,z, file_name, UpperTrail[r], LowerTrail[r],  [NewZeros0[n*(r-1):n*(r)], NewZeros1[n*(r-1):n*r]] if r>0  else None, index=model._offset+r+len(Backward_rounds)-1)
        drawTransition(z, file_name,model._offset+r+len(Backward_rounds))     

   

    for r in range(1,len(Forward_rounds)) :
        z = -l*(len(UpperTrail)-1)-l*r
        drawGrid(0, z, file_name,[0]*n, Forward_rounds[r],    None)
        NeededGrid(0,z,file_name, Forward_NeededKR[r])   
              
        if r+1 < len(Forward_rounds):
            drawTransition(z, file_name,model._offset+len(Backward_rounds)+len(UpperTrail)+r-1)     

     



    with open(file_name, "a") as f:
        f.write('\\end{tikzpicture}\n\\end{document}\n')

 

