COLOR_FORWARD_DISTINGUISHER = "WildStrawberry!80"
COLOR_BACKWARD_DISTINGUISHER = "NavyBlue!80"
COLOR_COL_NEW_ZEROS = "ForestGreen!90"



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

def drawFeistel(y, w,file_name ) :
    with open(file_name, "a") as f:
        f.write(f"\\draw[->]({w//2},{y}) -- ++(0,-1) -- ++(5,0) node[midway, draw, fill =white] "+"{ S } ;\n")
        f.write(f"\\node[inner sep=0] (X{y}) at  ({w+10+w//2},{y-1}) "+ "{ $ \\bigoplus $} ;\n")
        f.write(f"\\draw[->]({w+10+w//2},{y}) -- (X{y}) ;\n")
        f.write(f"\\draw[->] (X{y}) -- ++ (0,-1) -- ({w//2},{y-2.5}) -- ++(0,-0.5);\n")
        f.write(f"\\draw[->]({w//2},{y-1}) -- ++(0,-1) -- ({w+10+w//2},{y-2.5})- -++(0,-0.5);\n")
        f.write(f"\\draw[->]({w+w//2+5},{y-1}) -- (X{y}) ;\n")




def draw(model, algo):

    rD = len(model._is_zero_forward)-1
    n = len(model._is_zero_forward[0][0])
    w = min(n//2, 32)

    file_name = f"{algo}_{rD}_{n}_{model._valid}.tex"


    UpperTrail = [[[round(model.cbGetSolution(model._is_zero_forward[r][a][j]))  for j in range(n)]  for a in range(3)] for r in range(rD+1)]
    LowerTrail = [[[round(model.cbGetSolution(model._is_zero_backward[r][a][j])) for j in range(n)]  for a in range(3)] for r in range(rD+1)]

    NewZeros = [round(model.cbGetSolution(x)) for x in model._NewZeros]
   

    with open(file_name, "w") as f:
        f.write(
            "\\documentclass{standalone}\n\\usepackage[dvipsnames]{xcolor}\n\\usepackage{tikz}\n\\usetikzlibrary{arrows}\n\\usetikzlibrary{calc}\n\\usetikzlibrary{positioning}\n")
        f.write("\\begin{document}\n")
        f.write("\\begin{tikzpicture}\n")

    for r in range(len(UpperTrail)) :

        drawGrid(0,- 4*r, file_name, UpperTrail[r][0], LowerTrail[r][0],  NewZeros[n*(r-1):n*(r)] if r>0  else None)
        drawGrid(w+10, - 4*r, file_name, UpperTrail[r][1], LowerTrail[r][1],  NewZeros[n*r:n*(r+1)] if r+1<len(UpperTrail)  else None )
        if r+1<len(UpperTrail) :
            drawGrid(w/2 + 5 , -4*r-1.5,file_name, UpperTrail[r][2], LowerTrail[r][2], NewZeros[n*r:n*(r+1)])      
            drawFeistel(-4*r, w , file_name)

    with open(file_name, "a") as f:
        f.write('\\end{tikzpicture}\n\\end{document}\n')


