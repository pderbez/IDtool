##  Provide the model for the deduction of new zeros from the values of differences on both side of a function

##  The input bits and output bits of the function are inactive or unknown (hence named 0/*)
##  An additional variable X is created. X = 0 if no new zero can be deduced, and 1 if a new zero can be deduced
##  getModel() provides a file (named name.esp") which can be fed into espresso to obtain the constraints for authorized difference propagation
##  The format is din+dout+X a with a==0 iff and only if the tuple (din,dout,X) is authorized.


from sage.crypto.sboxes import sboxes
from sage.crypto.sbox import SBox
from collections import defaultdict
from itertools import product



# Conversion Int <--> Vectors
def convert_to_vector(I, L):
    return vector(GF(2), L, ZZ(I).digits(2, padto=L))


def convert_to_int(v):
    return sum(2 ** i * ZZ(v[i]) for i in range(len(v)))


# Describe the smallest subspace which can be described only with zeros and *  (for exemple **0**0)  which contains V .
def printVectorSpaceasString(V, m):
    S = ["1" for _ in range(m)]
    for i in range(m):
        A = [x for x in V.basis() if x[i] == 1]
        if len(A) == 0:
            S[i] = "0"
    return ''.join(S)




# Construct the set of vector v||w such that there exists for which S(x)+S(x+v) = w
def getExtendedDDT(S):
    m = S.m
    n= S.n
    DDT = S.difference_distribution_table()
    EDDT = set()
    for diff_input in range(DDT.nrows()):
        diffs_input = list(convert_to_vector(diff_input, m))
        for diff_output in range(DDT.ncols()):
            if DDT[diff_input, diff_output] != 0:
                diffs_output = list(convert_to_vector(diff_output, n))
                EDDT.add(tuple(vector(diffs_input+diffs_output)))
    return EDDT

# For all combinations of patterns of input and outputs , we verify if a stricter pattern could be applied (ie more zeros)
def exploitExtendedDDT(E, m,n, name):
    # strE = ["".join('1' if t == 1 else '0' for t in X) for X in E]
    # print(strE)
    f = open(name+".esp", 'w')
    f.write(f".i {m+n+1}\n.o 1\n.p {2**(m+n)}\n")
    V = VectorSpace(GF(2), m+n)
    # B= {}
    for target in product(GF(2), repeat=m+n):
        matching_diffs = [d for d in E if len(
            [i for i in range(m+n) if target[i] == 0 and d[i] != 0]) == 0]
        
        W = V.subspace(matching_diffs)
        StringTarget = "".join('1' if t == 1 else '0' for t in target)
        
        # New Zeros appears in W: the pattern is not optimal
        if printVectorSpaceasString(W, m+n) != StringTarget:
            if target[-n:] != tuple([0]*n) and target[:m]!= tuple([0]*m):
                print(StringTarget, printVectorSpaceasString(W,2*m))
            f.write(StringTarget+"0 1\n")

        # The pattern is already optimal
        else:
            f.write(StringTarget+"1 1\n")

    f.write(f".e\n")
    f.close()



def analyse(S, name):
    print(f"=============== {name} ==================")
    A = getExtendedDDT(S)
    exploitExtendedDDT(A, S.m,S.n, name)


def MixColumnSkinny():
    L = []
    for x in range(2 ** 4):
        v = convert_to_vector(x, 4)
        y = [v[0]+v[2]+v[3], v[0], v[1]+v[2], v[0]+v[2]]
        L.append(convert_to_int(y))
    return SBox(L)



def MixColumnMidori() :
    L = []
    for x in range(2 ** 4):
        v = convert_to_vector(x, 4)
        y = [v[1]+v[2]+v[3],v[0]+v[2]+v[3], v[0]+v[1]+v[3],v[0]+v[1]+v[2]]
        L.append(convert_to_int(y))
    return SBox(L)




def FeistelFunctionSimon() :
    L = []
    for x in range(2**4) :
        v = convert_to_vector(x,4)
        L.append(v[0]*v[1]+v[2]+v[3])
    return SBox(L)


# analyse(MixColumnSkinny(), 'MC_Skinny')


# analyse(MixColumnMidori(),'MC_Midori')

# analyse(sboxes["PRESENT"],"PRESENT")
