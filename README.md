# IDtool

This repository goes along the article *Minimalist model for Impossible Differentials*

It provides implementation of Gurobi Models to search for impossible differential distinguisher/attacks. 


| cipher | Distinguisher  | Attack | 
|--------|----------------|--------|
| AES    |   x            |      x |
| ARADI  |   x            |      x |
| Midori |   x            |        |
|PRESENT |   x            |        |
| SIMECK |   x            |        |
| SIMON  |   x            |      x |
| SKINNY |   x            |      x |
| SPECK  |   x            |        |



* Note pour Patrick : j'ai commité la version probabiliste pour ARADI. Il faudra probablement l'enlever pour la soumission


Most of them are written in Python. Some are in C++. All of them require a valid installation and licence of Gurobi. Most of them also provide tools to generate a graphical representation (in latex) of the distinguisher/attacks.


The repository  also contains a *Tool* directory.
It contains Sage scripts that were useful to determine modelisation of elementary functions of the blockciphers.