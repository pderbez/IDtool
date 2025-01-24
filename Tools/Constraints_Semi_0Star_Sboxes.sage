##  Deal with the case where the Sboxes is not considered in a truncated way
##  The  input bits are inactive or active (hence named 0/1)
##  The  output bits are inactive or unknown (hence named 0/*)
##  It allows to deal with the first round and last round of the distinguishers for which the inputs are known exactly.

##  getModel() provides a file (named "S_"+name+"Semi_Min_Diff.esp") which can be fed into espresso to obtain the constraints for authorized difference propagation


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



# Conversion Int <--> Vectors
def convert_to_string(I, L):
    return "".join(str(x) for x in ZZ(I).digits(2, padto=L))


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
        ADDT[convert_to_string(diff_input,m)] = V.subspace(diffs_output)

    return ADDT



# Describe the smallest subspace which can be described only with zeros and *  (for exemple **0**0)  which contains V .
def printVectorSpaceasString(V, m):
    S = ["1" for _ in range(m)]
    for i in range(m):
        A = [x for x in V.basis() if x[i] == 1]
        if len(A) == 0:
            S[i] = "0"
    return ''.join(S)






                
                
def getModel(S, name):
    print(f"=============== {name} ==================")
    m = S.input_size()
    A = getVectorSpaceDDT(S, m)
   
    f = open("S_"+name+"_Semi_Min_Diff.esp", 'w')
    f.write(f".i {2*m}\n.o 1\n.p {len(A)*(2**m)}\n")

    ListT = ["".join(x) for x in product(["0","1"],repeat=m)]
    
    for Din in sorted(A.keys(), key=lambda x: x.count("0")):       
        Dout = printVectorSpaceasString(A[Din],m)        
        
        if Dout !="1"*m  or Din=="1"*m:
            f.write(Din+Dout+" 0\n")
            print(Din,Dout)
            for y in ListT :
                if y!=Dout :
                    f.write(Din+y+" 1\n")
        else :
            f.write(Din+"-"*m+" 1\n")
                
    f.write(f".e\n")
    f.close()


S = sboxes["PRESENT"]
getModel(S,"PRESENT")

