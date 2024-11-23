COLOR_FORWARD_DISTINGUISHER = "WildStrawberry!80"
COLOR_BACKWARD_DISTINGUISHER = "NavyBlue!80"
COLOR_COL_NEW_ZEROS = "ForestGreen!90"



def drawGrid(y, file_name, UpperTrail, LowerTrail, NewZeros, extremeF, extremeB) :
    with open(file_name, "a") as f:
        for k in range(16):
            if sum(UpperTrail[4*k:4*k+4]) == 4  and extremeF:
                f.write(f"\\draw[fill={COLOR_FORWARD_DISTINGUISHER},draw opacity=0] ({k*2},{y}) -- ++(0,1) --++(2,0) --  cycle ;\n")
            else :
                for i in range(4) :
                    j= 4*k+i
                    if UpperTrail[j] == 1:
                        f.write(f"\\draw[fill={COLOR_FORWARD_DISTINGUISHER},draw opacity=0] ({j*0.5},{y}) -- ++(0,1) --++(0.5,0) --  cycle ;\n")
            
            if sum(LowerTrail[4*k:4*k+4]) == 4  and extremeB:
                f.write(f"\\draw[fill={COLOR_BACKWARD_DISTINGUISHER},draw opacity=0] ({k*2},{y}) -- ++(2,0) --++(0,1) --  cycle ;\n")
            else :
                for i in range(4) :
                    j= 4*k+i
                    if LowerTrail[j] == 1 :
                        f.write(f"\\draw[fill={COLOR_BACKWARD_DISTINGUISHER},draw opacity=0] ({j*0.5},{y}) -- ++(0.5,0) --++(0,1) --  cycle ;\n")
    
        for j in range(16):
            f.write(f"\\draw ({2*j},{y}) rectangle  ++ (2,1); \n")

        if NewZeros is not None :
            for j in range(16) :
                if NewZeros[j]!=0 :
                    f.write(f"\\draw[draw={COLOR_COL_NEW_ZEROS}, ultra thick]({2*j},{y-0.1}) rectangle  ++ (2,2.7); \n")

def drawBox(y, z,file_name, text) :
    with open(file_name, "a") as f:
        f.write(f"\\draw[->]({0},{y}) -- ++(-1,0) -- ++(0,-{z})  node[midway, draw=black,fill=white] "+"{" + text+"} -- ++ (1,0);\n")


def draw(file_name, model):

    UpperTrail = [[[round(model.cbGetSolution(model._is_zero_forward[r][a][j]))  for j in range(64)]  for a in range(2)] for r in range(len(model._is_zero_forward))]
    LowerTrail = [[[round(model.cbGetSolution(model._is_zero_backward[r][a][j])) for j in range(64)]  for a in range(2)] for r in range(len(model._is_zero_forward))]

    NewZeros = [round(model.cbGetSolution(x)) for x in model._NewZeros]
   

    with open(file_name, "w") as f:
        f.write(
            "\\documentclass{standalone}\n\\usepackage[dvipsnames]{xcolor}\n\\usepackage{tikz}\n\\usetikzlibrary{arrows}\n\\usetikzlibrary{calc}\n\\usetikzlibrary{positioning}\n")
        f.write("\\begin{document}\n")
        f.write("\\begin{tikzpicture}\n")

    for r in range(len(UpperTrail)) :
        drawGrid(- 3.5*r, file_name, UpperTrail[r][0], LowerTrail[r][0], None  , r==0 , False)
        drawBox(-3.5*r+0.4 , 1.4, file_name, "SubBox" )
        drawGrid(- 3.5*r -1.5, file_name, UpperTrail[r][1], LowerTrail[r][1], NewZeros[16*r:16*(r+1)] if r+1<len(UpperTrail)  else None,False,r+1 ==len(UpperTrail))
      
        if r+1 <len(UpperTrail) :
            drawBox(-3.5*r-1.1, 1.9, file_name, "Shuffle" )

    with open(file_name, "a") as f:
        f.write('\\end{tikzpicture}\n\\end{document}\n')


