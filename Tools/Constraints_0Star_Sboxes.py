##  Deal with the case where the Sboxes is not considered in a truncated way

##  The input bits and output bits are inactive or unknown (hence named 0/*)
##  analyse() provides the files in the folder StarModels : a synthetic way to see extraordinary behavious
##  getModel() provides a file (named "S_"+name+"_Min_Diff.esp") which can be fed into espresso to obtain the constraints for authorized difference propagation


from string import ascii_letters
from sage.crypto.sboxes import sboxes
from sage.crypto.sbox import SBox
from collections import defaultdict
from itertools import product


# Conversion Int <--> Vectors
def convert_to_vector(I, L):
    return vector(GF(2), L, ZZ(I).digits(2, padto=L))


def convert_to_int(v):
    return sum(2 ** i * ZZ(v[i]) for i in range(len(v)))


#  Test if the vector space V is included in a strict subspace which can be described only with zeros and *
def test_eq(V, m):
    # check if some zero appear
    return any(i for i in range(m) if all(x[i] == 0 for x in V.basis()))

#For each possible input difference din, construct A[Vect(din)] : the smallest vectorspace which contain all the differences S(x+din)+S(x)
def getVectorSpaceDDT(S, m):
    DDT = S.difference_distribution_table()
    ADDT = {}
    V = VectorSpace(GF(2), m)
    for diff_input in range(DDT.nrows()):
        diffs_output = [convert_to_vector(diff_output, m) for diff_output in range(DDT.nrows()) if DDT[diff_input, diff_output] != 0]
        ADDT[V.subspace([convert_to_vector(diff_input, m)])] = V.subspace(diffs_output)

    return ADDT

# The goal is to build A a dictionnary V:A[V] such that if din is in V then S(x+din)+S(x) is in A[V], with A[V] being a astrict subspace of the ambiant space
# At the beginning, we have such an A but only for V of dimension 1 (built from DDT)
def exploitVectorDDT(A, m):
    A = {x: A[x] for x in A if test_eq(A[x],m)  }
    dim1 = {tuple(x.basis()[0]): A[x] for x in A if A[x].dimension() > 0}
    l = 0
    d = 1
    seen = set(A.keys())

    V = VectorSpace(GF(2), m)
    while l != len(A) :
        print(f"collected {len(A)} useful relations, input vectorspaces have dimension up to {max(x.dimension() for x in A)}")
        l = len(A)

        for c1 in dim1:
            vec_c1 = vector(c1)
            for c2 in {x for x in A if x.dimension() == d}:

                if vec_c1 not in c2:

                    W = c2 + V.subspace([vec_c1])
                    if W not in seen:
                        seen.add(W)
                        if test_eq(W, m):
                            try:
                                AW = A[c2]+sum(A[V.subspace([x+vec_c1])]  for x in c2) # Calcule sum(A[V.subspace([x])] for x in W) mais en enlevant |c2|-1 termes.

                                if  test_eq(AW, m):
                                    A[W] = AW
                                    if len(A) % 100 == 0:
                                        print(f"collected {len(A)} useful relations, input vectorspaces have dimension up to {max(x.dimension() for x in A)}")
                                    if len(A) >= 3000:
                                        print("Cut the search as there are too many relations")
                                        return clean(A)

                            except KeyError as e:
                                pass

        d += 1
    C = {V:A[V] for V in A if  printVectorSpaceasString(V,m).count("*") == V.dimension() }
    C = clean(C)
    return C

# A is a dictionnary V:A[V] such that if din is in V then S(x+din)+S(x) is in A[V], with A[V] being a astrict subspace of the ambiant space
# We remove all the occurences V:A[V] such that there exist W:A[W] with V a subspace of W and A[V]==A[W] since it corresponds to a redondant value.
def clean(A):
    l = len(A)
    B = defaultdict(list)
    for x in A:
        B[A[x]].append(x)

    for out in B:
        B[out] = sorted(B[out], key=lambda x: x.dimension(), reverse=True)
        L = []
        for x in B[out]:
            if all(y+x != y for y in L):
                L.append(x)
            else:
                A.pop(x)
    print(f"Cleaned :  {l} relations can be summed up in {len(A)} relations")
    return A


# Describe the smallest subspace which can be described only with zeros and *  (for exemple **0**0)  which contains V .
def printVectorSpaceasString(V, m):
    S = ["*" for _ in range(m)]
    for i in range(m):
        A = [x for x in V.basis() if x[i] == 1]
        if len(A) == 0:
            S[i] = "0"
    return ''.join(S)




def wrap_analyse(name):
    analyse(sboxes[name], name)


def analyse(S, name):
    print(f"=============== {name} ==================")
    m = S.m
    A = getVectorSpaceDDT(S, m)
    B = exploitVectorDDT(A, m)
    if len(B) > 1:
        with open("StarModels/"+name, "w") as f:
            for V in sorted(B.keys(), key=lambda x: x.dimension()):
                # For the subspace of inputs V, we need that the containing subset is equal to V
                stringV = printVectorSpaceasString(V,m)
                if stringV.count("*") == V.dimension(): 
                    f.write(f"{stringV}-> {printVectorSpaceasString(B[V],m)}\n")
                

                
                
def getModel(S, name):
    print(f"=============== {name} ==================")
    m = S.m
    A = getVectorSpaceDDT(S, m)
    B = exploitVectorDDT(A, m)
    f = open("S_"+name+"_Min_Diff.esp", 'w')
    f.write(f".i {2*m}\n.o 1\n.p {len(A)*(2**m)}\n")

    ListT = ["".join(x) for x in product(["0","1"],repeat=m)]
    
    for V in sorted(A.keys(), key=lambda x: x.dimension()):
        # For the subspace of inputs V, we need that the containing subset is equal to V
        L = [W for W in B if W+V == W]
        Din = printVectorSpaceasString(V,m)
        if len(L)>0 :
            W = sorted(L,key=lambda x:x.dimension())[0]
            Dout = printVectorSpaceasString(B[W],m) 
        else :
            Dout = '1'*m
        f.write(Din+Dout+" 0\n")
        for y in ListT :
            if y!=Dout :
                f.write(Din+y+" 1\n")
    f.write(f".e\n")
    f.close()


# Midori128 Sboxes 
pi1 = [4, 1, 6, 3, 0, 5, 2, 7]
pi2 = [1, 6, 7, 0, 5, 2, 3, 4]
pi3 = [2, 3, 4, 1, 6, 7, 0, 5]
pi4 = [7, 4, 1, 2, 3, 0, 5, 6]


def Sbox_Midori(pi):
    S = sboxes["Midori_Sb1"]
    SSb = []
    for x in range(2 ** 8):
        v = convert_to_vector(x, 8)
        v = [v[pi[i]] for i in range(8)]
        v = list(convert_to_vector(S[convert_to_int(v[:4])], 4)) + \
            list(convert_to_vector(S[convert_to_int(v[4:])], 4))
        v = [v[pi.index(i)] for i in range(8)]
        SSb.append(convert_to_int(v))
    return SBox(SSb)



# Check all Sboxes
for name in sboxes:
    if sboxes[name].m <= 5:
        wrap_analyse(name)

# SSb0 = Sbox_Midori(pi1)
# SSb1 = Sbox_Midori(pi2)
# SSb2 = Sbox_Midori(pi3)
# SSb3 = Sbox_Midori(pi4)

# analyse(SSb0, "Midori_SSb0")
# analyse(SSb1, "Midori_SSb1")
# analyse(SSb2, "Midori_SSb2")
# analyse(SSb3, "Midori_SSb3")


# wrap_analyse("Midori_Sb1")
# print(sboxes["Ascon"].inverse())
# analyse(sboxes["Ascon"].inverse(),"ASCON_Inverse")


# S = sboxes["PRESENT"]
# analyse(S,"PRESENT")

