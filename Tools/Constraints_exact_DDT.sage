##  Deal with the case where the Sboxes is not considered in a truncated way

##  The input bits and output bits are inactive or active (hence named 0/1)
##  getModel() provides a file (named "S_"+name+"Diff.esp") which can be fed into espresso to obtain the constraints for authorized difference propagation


from string import ascii_letters
from sage.crypto.sboxes import sboxes
from sage.crypto.sbox import SBox
from collections import defaultdict
from itertools import product


# Conversion Int <--> Vectors
def convert_to_string(I, L):
    return "".join(str(x) for x in ZZ(I).digits(2, padto=L))


                
def getModel(S, name):
    print(f"=============== {name} ==================")
    m = S.input_size()

    f = open("S_"+name+"Diff.esp", 'w')
    f.write(f".i {2*m}\n.o 1\n.p {(2**(2*m))}\n")

    DDT = S.difference_distribution_table()
    for diff_input in range(DDT.nrows()):
        
        for diff_output in range(DDT.nrows()) :
            if  DDT[diff_input, diff_output] != 0 :
                f.write(convert_to_string(diff_input,m)+convert_to_string(diff_output,m)+" 0\n" )
            else :
                f.write(convert_to_string(diff_input,m)+convert_to_string(diff_output,m)+" 1\n" )


    f.write(f".e\n")
    f.close()

getModel(sboxes["PRESENT"],"PRESENT")