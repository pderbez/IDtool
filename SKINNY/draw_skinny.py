COLOR_FORWARD_DISTINGUISHER = "WildStrawberry!80"
COLOR_BACKWARD_DISTINGUISHER = "NavyBlue!80"
COLOR_COL_NEW_ZEROS = "ForestGreen!90"
COLOR_INVOLVED_CELLS_F = "yellow!50"
COLOR_INVOLVED_CELLS_B = "green!50"
COLOR_VALUE_NEEDED_F = "blue!60"

N=4


def drawGrid(state, x, y, file_name, color):
    with open(file_name, "a") as f:
        for j in range(16):
            if state[j] == 1:
                if color == COLOR_FORWARD_DISTINGUISHER:
                    f.write(f"\\draw[fill={color},draw opacity=0] ({
                            x+j % 4},{y-(j//4)})--++(0,1)--++(1,0)--  ({x+j % 4},{y-(j//4)});\n")
                elif color == COLOR_BACKWARD_DISTINGUISHER:
                    f.write(f"\\draw[fill={color},draw opacity=0] ({
                            x+j % 4},{y-(j//4)})--++(1,0)--++(0,1)--  ({x+j % 4},{y-(j//4)});\n")
                elif color == COLOR_VALUE_NEEDED_F:
                    f.write(f"\\draw[draw={COLOR_VALUE_NEEDED_F},ultra thick] ({
                            x+j % 4},{y-(j//4)+1})--++(1,-1);\n")
                else:
                    f.write(f"\\draw[fill={color}] ({x+j %
                            4},{y-(j//4)}) rectangle++(1,1);\n")
            f.write(f"\\draw ({x+j % 4},{y-(j//4)}) rectangle++(1,1);\n")


def drawGridKey(state_value, key, mapK, x, y, file_name):
    with open(file_name, "a") as f:
        if y<-20 :
            for j in range(8):
                if state_value[j] >= 1 and key[j] >= 1:
                    f.write(f"\\draw[draw={COLOR_VALUE_NEEDED_F},ultra thick] ({
                            x+j % 4},{y-(j//4)+1})--++(1,-1);\n")
                f.write(f"\\draw ({
                        x+j % 4},{y-(j//4)}) rectangle++(1,1) node[midway] "+"{"+f"{hex(mapK[j])[2:]}"+"};\n")
        else:
            T = dict()
            for j in range(4):
                T[j] = j
                T[j+4] = j
                T[j+12] = j
            T[8] = 7
            T[9] = 4
            T[10] = 5
            T[11] = 6
            for j in range(16):

                if state_value[j] >= 1 and key[T[j]] >= 1:

                    f.write(f"\\draw[draw={COLOR_VALUE_NEEDED_F},ultra thick] ({
                            x+j % 4},{y-(j//4)+1})--++(1,-1);\n")
                f.write(f"\\draw ({
                        x+j % 4},{y-(j//4)}) rectangle++(1,1) node[midway] "+"{"+f"{hex(mapK[T[j]])[2:]}"+"};\n")
        f.write(f"\\draw[->]")
        f.write(f"({x+2},{y+2}-1)--++(0,3);")


def drawSTKey(key, mapK, x, y, file_name):
    with open(file_name, "a") as f:
        for j in range(8):  # 16) :
            if key[j] == 1:
                f.write(f"\\draw[draw={COLOR_VALUE_NEEDED_F},ultra thick] ({
                        x+j % 4},{y-(j//4)+1})-- ++(1,-1);\n")
            f.write(f"\\draw ({
                    x+j % 4},{y-(j//4)}) rectangle++(1,1) node[midway] "+"{"+f"{hex(mapK[j])[2:]}"+"};\n")


def drawF(name, x, y, file_name, dir=0):
    with open(file_name, "a") as f:
        # if dir==0 :
        #     f.write(f"\\draw[<->]")
        # elif dir==1 :
        f.write(f"\\draw[->]")
        # else :
        #     f.write(f"\\draw[<-]")

        f.write(
            f"({x},{y}-1)--++(2,0)   node[midway, draw=black,fill=white] "+"{"+name+"};\n")
        
def drawCurveF(name, x, y, file_name, dir=0,long=False):
    with open(file_name, "a") as f:
       
        f.write(f"\\draw[->]")
       

        f.write(
            f"({x},{y}-1)--++(2,0)   node[midway, draw=black,fill=white] "+"{"+name+"} "+f" -- ++(0,-3 {"-5" if long else ""}) -- (-1,{y -4 -5 *long})-- ++ (0,-3) -- ++ (1,0);\n")


def drawTrail(trail, y, file_name, dir, color, x=0):
    for r in range(len(trail)):
        drawGrid(trail[r][0], x+18*(r %N), y-6*(r//N), file_name, color)
        drawF("SC", x+18*(r %N)+4, y-6*(r//N), file_name, dir)
        drawGrid(trail[r][1], x+18*(r %N)+6, y-6*(r//N), file_name, color)
        drawF("SR", x+18*(r %N)+10, y-6*(r//N), file_name, dir)
        drawGrid(trail[r][2], x+18*(r %N)+12, y-6*(r//N), file_name, color)
        if (r+1)%N !=0  :
            drawF("MC", x+18*(r %N)+16, y- 6*(r//N), file_name, dir)
        else :
            drawCurveF("MC", x+18*(r %N)+16, y- 6*(r//N), file_name, dir)


def drawTrailKeyRecovery(trail, trail_value, y, file_name, dir, color, x, key, mapK):
    for r in range(len(trail)):

        drawGrid(trail[r][0], x+18*(r %N), y-6*(r//N), file_name, color)
        drawGrid(trail_value[r][0], x+18*(r %N), y -6*
                 (r//N), file_name, COLOR_VALUE_NEEDED_F)

        if not (color == COLOR_INVOLVED_CELLS_F and r == len(trail)-1):
            drawF("SC", x+18*(r %N)+4, y-6*(r//N), file_name, dir)

            drawGrid(trail[r][1], x+18*(r %N)+6,
                     y-6*(r//N), file_name, color)
            drawGrid(trail_value[r][1], x+18*(r %N)+6, y-6*(r//N),
                     file_name, COLOR_VALUE_NEEDED_F)

            drawF("SR", x+18*(r %N)+10, y-6*(r//N), file_name, dir)
            drawGrid(trail[r][2], x+18*(r %N)+12,
                     y-6*(r//N), file_name, color)
            drawGrid(trail_value[r][2], x+18*(r %N)+12, y-6*(r//N),
                     file_name, COLOR_VALUE_NEEDED_F)
            
            if r!= len(trail)-1:
                drawF("MC", x+18*(r %N)+16, y-6*(r//N), file_name, dir)
            else :
                print(r)
                drawCurveF("MC", x+18*(r %N)+16, y-6*(r//N), file_name, dir, long=True)

        if color == COLOR_INVOLVED_CELLS_B:
            if r > 0:
                drawGridKey(trail_value[r][0], key[r-1],
                            mapK[r-1], x+18*(r %N)+6-3.5, y-5-6*(r//N), file_name)
        else:
            if r+1 < len(trail):
                drawGridKey(trail_value[r][1], key[r+1],
                            mapK[r+1], x+18*(r %N)+2.5+6, y-5-6*(r//N), file_name)


def drawZeros(newZeros, y, file_name):
    with open(file_name, "a") as f:
        for j in range(len(newZeros)):
            if newZeros[j] == 1:
                r = j//4
                f.write(f"\\draw[draw={COLOR_COL_NEW_ZEROS},ultra thick, fill={
                        COLOR_COL_NEW_ZEROS}, fill opacity=0.2] ({18*((r+1)%N)+j % 4},{y-6*((r+1)//N)+1+0.1}) rectangle++(1,-4.2);\n")
                f.write(f"\\draw[draw={COLOR_COL_NEW_ZEROS},ultra thick,fill={
                        COLOR_COL_NEW_ZEROS},fill opacity=0.2] ({18*(r%N)+12+j % 4},{y-6*(r//N)+1.1}) rectangle++(1,-4.2);\n")


def draw(is_zero_f, is_zero_b, newZeros, summary, TruncB_value, TruncF_value, STKey, Count_Key, KeySchedule, file_name):
    file_name = file_name
    with open(file_name, "w") as f:
        f.write(
            "\\documentclass{standalone}\n\\usepackage[dvipsnames]{xcolor}\n\\usepackage{tikz}\n\\usetikzlibrary{arrows}\n\\usetikzlibrary{calc}\n\\usetikzlibrary{positioning}\n")
        f.write("\\begin{document}\n")
        f.write("\\begin{tikzpicture}\n")
    rB = len(TruncB_value)
    rF = len(TruncF_value)
    rD = len(is_zero_f)-1

    drawTrailKeyRecovery(summary[:rB], TruncB_value, 0, file_name,-1,
                         COLOR_INVOLVED_CELLS_B,0, STKey, KeySchedule)
    drawTrail(is_zero_f,- 11*(rB//N+1), file_name,
              1, COLOR_FORWARD_DISTINGUISHER)
    drawTrail(is_zero_b, -11*(rB//N+1), file_name,-
              1, COLOR_BACKWARD_DISTINGUISHER)
    drawTrailKeyRecovery(summary[rB+rD+1:], TruncF_value, -11*(rB//N+1)-6*(rD//N+1), file_name, 1,
                         COLOR_INVOLVED_CELLS_F,0, STKey[-rF-1:], KeySchedule[-rF-1:])

    drawZeros(newZeros, - 11*(rB//N+1), file_name)


    with open(file_name, "a") as f:
        f.write('\\end{tikzpicture}\n\\end{document}\n')
