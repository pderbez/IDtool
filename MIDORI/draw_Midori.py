COLOR_FORWARD_DISTINGUISHER = "WildStrawberry!80"
COLOR_BACKWARD_DISTINGUISHER = "NavyBlue!80"
COLOR_COL_NEW_ZEROS = "ForestGreen!90"



def drawGrid(x,y, file_name, UpperTrail, LowerTrail, NewZeros) :
    with open(file_name, "a") as f:
        for j in range(16):
            for k in range(8) :
                if UpperTrail[j][k]== 0:
                    f.write(f"\\draw[fill={COLOR_FORWARD_DISTINGUISHER},draw opacity=0] ({x+4*(j//4)+k*0.5},{y-(j%4)}) -- ++(0,1) --++(0.5,0) --  cycle ;\n")
                if LowerTrail[j][k] == 0 :
                    f.write(f"\\draw[fill={COLOR_BACKWARD_DISTINGUISHER},draw opacity=0] ({x+4*(j//4)+k*0.5},{y-(j%4)}) -- ++(0.5,0) --++(0,1) --  cycle ;\n")
        
        for j in range(16):
            f.write(f"\\draw ({x+4*(j//4)},{y-(j%4)}) rectangle  ++ (4,1); \n")

        if NewZeros is not None :
            for j in range(32) :
                if NewZeros[j]!=0 :
                    f.write(f"\\draw[draw={COLOR_COL_NEW_ZEROS}, ultra thick]({x+j/2},{y-3.2}) rectangle  ++ (0.5,4.4); \n")

def drawBox(x,y, file_name, text) :
    with open(file_name, "a") as f:
        f.write(f"\\draw[->]({x},{y}) -- ++(4,0)  node[midway, draw=black,fill=white] "+"{" + text+"};\n")

def drawCurveBox(x,y, file_name, text) :
    with open(file_name, "a") as f:
        f.write(f"\\draw[->]({x},{y}) -- ++(2,0) -- ++(0,-3)  node[midway, draw=black,fill=white] "+"{" + text+"}  -- ++ (-60,0) -- ++ (0,-3) -- ++ (2,0)  ;\n")


def draw(model, file_name):
    UpperTrail = [[[[round(model.cbGetSolution(model._is_zero_f[a][r][j][k])) for k in range(8)] for j in range(16)] for r in range(len(model._is_zero_f[0]))] for a in range(3)]
    LowerTrail = [[[[round(model.cbGetSolution(model._is_zero_b[a][r][j][k])) for k in range(8)] for j in range(16)] for r in range(len(model._is_zero_f[0]))] for a in range(3)]

    NewZeros = [round(model.cbGetSolution(x)) for x in model._NewZerosMC]

    with open(file_name, "w") as f:
        f.write(
            "\\documentclass{standalone}\n\\usepackage[dvipsnames]{xcolor}\n\\usepackage{tikz}\n\\usetikzlibrary{arrows}\n\\usetikzlibrary{calc}\n\\usetikzlibrary{positioning}\n")
        f.write("\\begin{document}\n")
        f.write("\\begin{tikzpicture}\n")

    for r in range(len(model._is_zero_f[0])) :
        drawGrid(0, - 6*r, file_name, UpperTrail[0][r], LowerTrail[0][r],NewZeros[32*(r-1):32*(r)] if r>0  else None  )
        drawBox(16, -6*r-1 , file_name, "SubCell")
        drawGrid(20, - 6*r, file_name, UpperTrail[1][r], LowerTrail[1][r], None)
        drawBox(36, -6*r-1 , file_name, "ShuffleCell")
        drawGrid(40, - 6*r, file_name, UpperTrail[2][r], LowerTrail[2][r], NewZeros[32*r:32*(r+1)] if r+1<len(model._is_zero_f[0]) else None )
        if r+1 <len(model._is_zero_f[0]) :
            drawCurveBox(56, -6*r-1 , file_name, "MixColumn")

    with open(file_name, "a") as f:
        f.write('\\end{tikzpicture}\n\\end{document}\n')


