#include <iostream>
#include <vector>
#include <set>


#include "/opt/gurobi912/linux64/include/gurobi_c++.h"

using namespace std;

void generateEQFA() {
    vector<unsigned> sb (8);
    for (unsigned a = 0; a < 8; ++a) {
        unsigned x = a & 1, y = (a >> 1) & 1, c = (a >> 2) & 1;
        unsigned z = x ^ y ^ c, cc = (x & y) ^ (c & (x^y));
        sb[a] = z | (cc << 1);
    }

    set<unsigned> valid_tr;

    for (unsigned x = 0; x < 8; ++x) {
        for (unsigned d = 0; d < 8; ++d) {
            valid_tr.emplace(d | ((sb[x] ^ sb[x^d]) << 3));
        }
    }

    for (unsigned x = 0; x < 32; ++x) {
        unsigned y = 0;
        for (auto z : valid_tr) {
            if ((x & z) == z) y |= z;
        }
        if (y != x) {
            for (unsigned i = 0; i < 5; ++i) cout << ((x >> i) & 1);
            cout << " --> ";
            for (unsigned i = 0; i < 5; ++i) cout << ((y >> i) & 1);
            cout << endl;
        }
    }
    getchar();

    for (auto x : valid_tr) {
        for (unsigned i = 0; i < 5; ++i) cout << ((x >> i) & 1);
        cout << endl;
    }
    cout << "valid: " << valid_tr.size() << endl;

    vector<unsigned> proba1 (8);
    for (auto x : valid_tr) {
        proba1[x & 7] |= (x >> 3);
    }
    for (unsigned a = 0; a < 8; ++a) {
        for (unsigned b = 0; b < 8; ++b) {
            if ((a & b) == a) proba1[b] |= proba1[a];
        }
    }
    for (unsigned a = 0; a < 8; ++a) {
        for (unsigned i = 0; i < 3; ++i) cout << ((a >> i) & 1);
        cout << ": ";
        for (unsigned i = 0; i < 2; ++i) cout << ((proba1[a] >> i) & 1);
        cout << endl;
    }

    for (unsigned a = 0; a < 32; ++a) {
        cout << "model.addConstr(";
        if (valid_tr.count(a) == 0) {
            if (((a >> 0) & 1) == 0) cout << " x ";
            else cout << " (1 - x) ";
            if (((a >> 1) & 1) == 0) cout << "+ y ";
            else cout << "+ (1 - y) ";
            if (((a >> 2) & 1) == 0) cout << "+ c ";
            else cout << "+ (1 - c) ";
            if (((a >> 3) & 1) == 0) cout << "+ z ";
            else cout << "+ (1 - z) ";
            if (((a >> 4) & 1) == 0) cout << "+ cc ";
            else cout << "+ (1 - cc) ";
            cout << " + v >= 1);" << endl;
        }
        else {
            if (((a >> 0) & 1) == 0) cout << " x ";
            else cout << " (1 - x) ";
            if (((a >> 1) & 1) == 0) cout << "+ y ";
            else cout << "+ (1 - y) ";
            if (((a >> 2) & 1) == 0) cout << "+ c ";
            else cout << "+ (1 - c) ";
            if (((a >> 3) & 1) == 0) cout << "+ z ";
            else cout << "+ (1 - z) ";
            if (((a >> 4) & 1) == 0) cout << "+ cc ";
            else cout << "+ (1 - cc) ";
            cout << " + (1-v) >= 1);" << endl;
        }
    }

} 

void addFA(GRBModel & model, GRBVar & x, GRBVar & y, GRBVar & c, GRBVar & z, GRBVar & cc) {
    model.addConstr((1 - x) + y + c + z + cc >= 1);
    model.addConstr(x + (1 - y) + c + z + cc >= 1);
    model.addConstr(x + y + (1 - c) + z + cc >= 1);
    model.addConstr((1 - x) + (1 - y) + (1 - c) + z + cc >= 1);
    model.addConstr(x + y + c + (1 - z) + cc >= 1);
    model.addConstr((1 - x) + (1 - y) + c + (1 - z) + cc >= 1);
    model.addConstr((1 - x) + y + (1 - c) + (1 - z) + cc >= 1);
    model.addConstr(x + (1 - y) + (1 - c) + (1 - z) + cc >= 1);
    model.addConstr((1 - x) + (1 - y) + (1 - c) + (1 - z) + cc >= 1);
    model.addConstr(x + y + c + z + (1 - cc) >= 1);
    model.addConstr((1 - x) + y + c + z + (1 - cc) >= 1);
    model.addConstr(x + (1 - y) + c + z + (1 - cc) >= 1);
    model.addConstr(x + y + (1 - c) + z + (1 - cc) >= 1);
    model.addConstr((1 - x) + (1 - y) + (1 - c) + z + (1 - cc) >= 1);
    model.addConstr(x + y + c + (1 - z) + (1 - cc) >= 1);
    model.addConstr((1 - x) + (1 - y) + c + (1 - z) + (1 - cc) >= 1);
    model.addConstr((1 - x) + y + (1 - c) + (1 - z) + (1 - cc) >= 1);
    model.addConstr(x + (1 - y) + (1 - c) + (1 - z) + (1 - cc) >= 1);
}

void addFA(GRBModel & model, GRBVar & x, GRBVar & y, GRBVar & c, GRBVar & z, GRBVar & cc, GRBLinExpr & new_zeros) {
    GRBVar v = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
    model.addConstr(v <= x + y + c + z + cc);
    model.addConstr(4-3*v >= x + y + c + z);
    new_zeros += v;
}

void modelSPECK(unsigned R, unsigned n) {

    GRBEnv env = GRBEnv(true);
    env.set("LogFile", "mip1.log");
    env.set(GRB_IntParam_OutputFlag, 0);
    env.start();

    GRBModel model = GRBModel(env);

    vector<GRBVar> forwardX_L (n*(R+1));
    vector<GRBVar> forwardX_R (n*(R+1));
    vector<GRBVar> forwardX_C (n*(R));
    vector<GRBVar> backwardX_L (n*(R+1));
    vector<GRBVar> backwardX_R (n*(R+1));
    vector<GRBVar> backwardX_C (n*(R));
    vector<GRBVar> X_L (n*(R+1));
    vector<GRBVar> X_R (n*(R+1));
    vector<GRBVar> X_C (n*(R));

    unsigned alpha = n-8, beta = n+3;



    for (auto & x : forwardX_L) x = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
    for (auto & x : forwardX_R) x = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
    for (auto & x : forwardX_C) x = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
    for (auto & x : backwardX_L) x = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
    for (auto & x : backwardX_R) x = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
    for (auto & x : backwardX_C) x = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
    for (auto & x : X_L) x = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
    for (auto & x : X_R) x = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
    for (auto & x : X_C) x = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);

    for (unsigned i = 0; i < X_L.size(); ++i) {
        model.addConstr(2*X_L[i] <= forwardX_L[i] + backwardX_L[i]);
        model.addConstr(X_L[i] + 1 >= forwardX_L[i] + backwardX_L[i]);
    }
    for (unsigned i = 0; i < X_R.size(); ++i) {
        model.addConstr(2*X_R[i] <= forwardX_R[i] + backwardX_R[i]);
        model.addConstr(X_R[i] + 1 >= forwardX_R[i] + backwardX_R[i]);
    }
    for (unsigned i = 0; i < X_C.size(); ++i) {
        model.addConstr(2*X_C[i] <= forwardX_C[i] + backwardX_C[i]);
        model.addConstr(X_C[i] + 1 >= forwardX_C[i] + backwardX_C[i]);
    }

    GRBLinExpr af = 0;
    for (unsigned i = 0; i < n; ++i) af += forwardX_L[i] + forwardX_R[i];
    model.addConstr(af >= 1);
    //model.addConstr(af == 1);

    GRBLinExpr ab = 0;
    for (unsigned i = 0; i < n; ++i) ab += backwardX_L[n*R + i] + backwardX_R[n*R + i];
    model.addConstr(ab >= 1);
    //model.addConstr(ab == 1);

    //model.addConstr( backwardX_R[n*R + 0] == 1);
    //model.addConstr( forwardX_L[26] == 1);


    for (unsigned r = 0; r < R; ++r) {
        model.addConstr(forwardX_C[n*r + n-1] == 0);
        for (unsigned i = 1; i < n; ++i) {
            model.addConstr(forwardX_C[n*r + i-1] == forwardX_L[n*(r+1) + i]);
            model.addConstr(3*forwardX_C[n*r + i-1] >= forwardX_L[n*r + (i + alpha)%n] + forwardX_R[n*r + i] + forwardX_C[n*r + i]);
            model.addConstr(forwardX_C[n*r + i-1] <= forwardX_L[n*r + (i + alpha)%n] + forwardX_R[n*r + i] + forwardX_C[n*r + i]);
        }
        model.addConstr(3*forwardX_L[n*(r+1)] >= forwardX_L[n*r + (alpha)%n] + forwardX_R[n*r] + forwardX_C[n*r]);
        model.addConstr(forwardX_L[n*(r+1)] <= forwardX_L[n*r + (alpha)%n] + forwardX_R[n*r] + forwardX_C[n*r]);

        if (r < R-1) {
            for (unsigned i = 0; i < n; ++i) {
                model.addConstr(2*forwardX_R[n*(r+1) + i] >= forwardX_L[n*(r+1) + i] + forwardX_R[n*r + (i + beta)%n]);
                model.addConstr(forwardX_R[n*(r+1) + i] <= forwardX_L[n*(r+1) + i] + forwardX_R[n*r + (i + beta)%n]);
            }
        }
        else {
            for (unsigned i = 0; i < n; ++i) {
                model.addConstr(forwardX_R[n*r + (i + beta)%n] == forwardX_R[n*(r+1) + i]);
            }
        }
    }

    for (unsigned r = 0; r < R; ++r) {
        if (r < R-1) {
            for (unsigned i = 0; i < n; ++i) {
                model.addConstr(2*backwardX_R[n*r + (i + beta)%n] >= backwardX_R[n*(r+1) + i] + backwardX_L[n*(r+1) + i] );
                model.addConstr(backwardX_R[n*r + (i + beta)%n] <= backwardX_R[n*(r+1) + i] + backwardX_L[n*(r+1) + i]);
            }
        }
        else {
            for (unsigned i = 0; i < n; ++i) {
                model.addConstr(backwardX_R[n*r + (i + beta)%n] == backwardX_R[n*(r+1) + i]);
            }
        }

        model.addConstr(backwardX_C[n*r + n-1] == 0);
        for (unsigned i = 1; i < n; ++i) {
            model.addConstr(backwardX_C[n*r + i-1] == backwardX_L[n*r + (i + alpha)%n]);
            model.addConstr(3*backwardX_C[n*r + i-1] >= backwardX_L[n*(r+1) + i] + backwardX_R[n*r + i] + backwardX_C[n*r + i]);
            model.addConstr(backwardX_C[n*r + i-1] <= backwardX_L[n*(r+1) + i] + backwardX_R[n*r + i] + backwardX_C[n*r + i]);
        }
        model.addConstr(3*backwardX_L[n*r + (alpha)%n] >=  backwardX_L[n*(r+1)] + backwardX_R[n*r] + backwardX_C[n*r]);
        model.addConstr(backwardX_L[n*r + (alpha)%n] <= backwardX_L[n*(r+1)] + backwardX_R[n*r] + backwardX_C[n*r]);   
    }

    GRBLinExpr new_zeros = 0;

    for (unsigned r = 0; r < R; ++r) {
        if (r < R-1) {
            for (unsigned i = 0; i < n; ++i) {
                GRBVar v = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
                model.addConstr(v <= X_R[n*r + (i + beta)%n] + X_R[n*(r+1) + i] + X_L[n*(r+1) + i]);
                model.addConstr(3 - 2*v >= X_R[n*r + (i + beta)%n] + X_R[n*(r+1) + i] + X_L[n*(r+1) + i]);
                new_zeros += v;
            }
        }
        for (unsigned i = 1; i < n; ++i) {
            addFA(model, X_L[n*r + (i + alpha)%n], X_R[n*r + i], X_C[n*r + i], X_L[n*(r+1) + i], X_C[n*r + i-1], new_zeros);
        }

        GRBVar v = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
        model.addConstr(v <= X_L[n*(r+1)] + X_L[n*r + (alpha)%n] + X_R[n*r] + X_C[n*r]);
        model.addConstr(4- 3*v >= X_L[n*(r+1)] + X_L[n*r + (alpha)%n] + X_R[n*r] + X_C[n*r]);
    }


    model.addConstr(new_zeros >= 1);

    GRBLinExpr obj = 0;
    for (unsigned i = 0; i < n; ++i) obj += forwardX_L[i] + forwardX_R[i] + backwardX_L[n*R + i] + backwardX_R[n*R + i];

    //model.setObjective(obj, GRB_MAXIMIZE);
    //model.setObjective(obj, GRB_MINIMIZE);
    model.setObjective(new_zeros, GRB_MAXIMIZE);

    double best_cluster = -1.0;

    unsigned candidates = 0;

    cout << "\r" << "trials: " << candidates << " " << flush;

    while (true) {
        model.optimize(); 
        if (model.get(GRB_IntAttr_Status) == GRB_OPTIMAL) {
            candidates += 1;
            cout << "\r" << "trials: " << candidates << " " << flush;
            
            //getchar();
            


            GRBModel model2 = GRBModel(env);

            vector<GRBVar> XX_L (n*(R+1));
            vector<GRBVar> XX_R (n*(R+1));
            vector<GRBVar> XX_C (n*(R));
            for (auto & x : XX_L) x = model2.addVar(0.0, 1.0, 0.0, GRB_BINARY);
            for (auto & x : XX_R) x = model2.addVar(0.0, 1.0, 0.0, GRB_BINARY);
            for (auto & x : XX_C) x = model2.addVar(0.0, 1.0, 0.0, GRB_BINARY);

            vector<GRBConstr> myconstr;

            for (unsigned i = 0; i < n; ++i) {
               if (forwardX_L[i].get(GRB_DoubleAttr_Xn) > 0.5) model2.addConstr(XX_L[i] == 1); 
               else myconstr.emplace_back(model2.addConstr(XX_L[i] == 0)); 
               if (forwardX_R[i].get(GRB_DoubleAttr_Xn) > 0.5) model2.addConstr(XX_R[i] == 1); 
               else myconstr.emplace_back(model2.addConstr(XX_R[i] == 0)); 
               if (backwardX_L[n*R + i].get(GRB_DoubleAttr_Xn) > 0.5) model2.addConstr(XX_L[n*R + i] == 1); 
               else myconstr.emplace_back(model2.addConstr(XX_L[n*R + i] == 0));
               if (backwardX_R[n*R + i].get(GRB_DoubleAttr_Xn) > 0.5) model2.addConstr(XX_R[n*R + i] == 1);
               else myconstr.emplace_back(model2.addConstr(XX_R[n*R + i] == 0));
            }
            for (unsigned r = 0; r < R; ++r) {
                if (r < R-1) {
                    for (unsigned i = 0; i < n; ++i) {
                        GRBVar v = model2.addVar(0.0, 1.0, 0.0, GRB_BINARY);
                        model2.addConstr(2*v == XX_R[n*r + (i + beta)%n] + XX_R[n*(r+1) + i] + XX_L[n*(r+1) + i]);
                    }
                }
                else {
                    for (unsigned i = 0; i < n; ++i) {
                        model2.addConstr(XX_R[n*r + (i + beta)%n] == XX_R[n*(r+1) + i]);
                    }
                }

                model2.addConstr(XX_C[n*r + n-1] == 0);
                for (unsigned i = 1; i < n; ++i) {
                    addFA(model2, XX_L[n*r + (i + alpha)%n], XX_R[n*r + i], XX_C[n*r + i], XX_L[n*(r+1) + i], XX_C[n*r + i-1]);
                }

                GRBVar v = model2.addVar(0.0, 2.0, 0.0, GRB_INTEGER);
                model2.addConstr(2*v == XX_L[n*(r+1)] + XX_L[n*r + (alpha)%n] + XX_R[n*r] + XX_C[n*r]);
            }
            model2.optimize();
            if (model2.get(GRB_IntAttr_Status) == GRB_OPTIMAL) {
                GRBLinExpr e = 0;
                for (unsigned i = 0; i < n; ++i) {
                    if (forwardX_L[i].get(GRB_DoubleAttr_Xn) < 0.5) e += forwardX_L[i]; 
                    else e += 1 - forwardX_L[i];  
                    if (forwardX_R[i].get(GRB_DoubleAttr_Xn) < 0.5) e += forwardX_R[i]; 
                    else e += 1 - forwardX_R[i]; 
                    if (backwardX_L[n*R + i].get(GRB_DoubleAttr_Xn) < 0.5) e += backwardX_L[n*R + i]; 
                    else e += 1 - backwardX_L[n*R + i]; 
                    if (backwardX_R[n*R + i].get(GRB_DoubleAttr_Xn) < 0.5) e += backwardX_R[n*R + i]; 
                    else e += 1 - backwardX_R[n*R + i]; 
                }
                model.addConstr(e >= 1);
                /*cout << " ---------- " << endl;
                for (unsigned r = 0; r <= R; ++r) {
                    for (unsigned i = 0; i < n; ++i) {
                    cout << (XX_L[n*r + i].get(GRB_DoubleAttr_Xn) < 0.5 ? 0 : 1);
                    }
                    cout << " ";
                    for (unsigned i = 0; i < n; ++i) {
                        cout << (XX_R[n*r + i].get(GRB_DoubleAttr_Xn) < 0.5 ? 0 : 1);
                    }

                    cout << endl;
                }*/
            }
            else {
                cout << endl;
                cout << "Solution found" << endl;
                /*for (auto & c : myconstr) model2.remove(c);

                GRBModel model3 = GRBModel(env);

                vector<GRBVar> XXX_L (2*n);
                vector<GRBVar> XXX_R (2*n);
                for (auto & x : XXX_L) x = model3.addVar(0.0, 1.0, 0.0, GRB_BINARY);
                for (auto & x : XXX_R) x = model3.addVar(0.0, 1.0, 0.0, GRB_BINARY);

                for (unsigned i = 0; i < n; ++i) {
                    if (forwardX_L[i].get(GRB_DoubleAttr_Xn) > 0.5) model3.addConstr(XXX_L[i] == 1); 
                    if (forwardX_R[i].get(GRB_DoubleAttr_Xn) > 0.5) model3.addConstr(XXX_R[i] == 1); 
                    if (backwardX_L[n*R + i].get(GRB_DoubleAttr_Xn) > 0.5) model3.addConstr(XXX_L[n + i] == 1); 
                    if (backwardX_R[n*R + i].get(GRB_DoubleAttr_Xn) > 0.5) model3.addConstr(XXX_R[n + i] == 1);
                }

                GRBLinExpr obj2 = 0;
                for (unsigned i = 0; i < n; ++i) obj2 += XX_L[i] + XX_R[i] + XX_L[n*R + i] + XX_R[n*R + i];
                model2.setObjective(obj2, GRB_MINIMIZE);
                model2.optimize();
                while (model2.get(GRB_IntAttr_Status) == GRB_OPTIMAL && model2.get(GRB_DoubleAttr_ObjVal) > 0.5)
                {
                    GRBLinExpr e = 0, f = 0;
                    for (unsigned i = 0; i < n; ++i) {
                        if (XX_L[i].get(GRB_DoubleAttr_Xn) > 0.5) e += 1-XX_L[i]; 
                        if (XX_R[i].get(GRB_DoubleAttr_Xn) > 0.5) e += 1-XX_R[i]; 
                        if (XX_L[n*R + i].get(GRB_DoubleAttr_Xn) > 0.5) e += 1-XX_L[n*R + i]; 
                        if (XX_R[n*R + i].get(GRB_DoubleAttr_Xn) > 0.5) e += 1-XX_R[n*R + i]; 

                        if (XX_L[i].get(GRB_DoubleAttr_Xn) > 0.5) f += 1-XXX_L[i]; 
                        if (XX_R[i].get(GRB_DoubleAttr_Xn) > 0.5) f += 1-XXX_R[i]; 
                        if (XX_L[n*R + i].get(GRB_DoubleAttr_Xn) > 0.5) f += 1-XXX_L[n + i]; 
                        if (XX_R[n*R + i].get(GRB_DoubleAttr_Xn) > 0.5) f += 1-XXX_R[n + i]; 
                    }

                    model2.addConstr(e >= 1);
                    model3.addConstr(f >= 1);
                    model2.optimize();
                }
                GRBLinExpr obj3 = 0;
                for (unsigned i = 0; i < n; ++i) obj3 += XXX_L[i] + XXX_R[i] + XXX_L[n + i] + XXX_R[n + i];
                model3.setObjective(obj3, GRB_MAXIMIZE);
                model3.optimize();

                if (model.get(GRB_DoubleAttr_ObjVal) - model3.get(GRB_DoubleAttr_ObjVal) > best_cluster) {
                    best_cluster = model.get(GRB_DoubleAttr_ObjVal) - model3.get(GRB_DoubleAttr_ObjVal);
                    model.addConstr(obj >= best_cluster + 1.0);
                }
                
                {
                    GRBLinExpr e = 0;
                    for (unsigned i = 0; i < n; ++i) {
                        if (forwardX_L[i].get(GRB_DoubleAttr_Xn) < 0.5) e += forwardX_L[i]; 
                        else e += 1 - forwardX_L[i];  
                        if (forwardX_R[i].get(GRB_DoubleAttr_Xn) < 0.5) e += forwardX_R[i]; 
                        else e += 1 - forwardX_R[i]; 
                        if (backwardX_L[n*R + i].get(GRB_DoubleAttr_Xn) < 0.5) e += backwardX_L[n*R + i]; 
                        else e += 1 - backwardX_L[n*R + i]; 
                        if (backwardX_R[n*R + i].get(GRB_DoubleAttr_Xn) < 0.5) e += backwardX_R[n*R + i]; 
                        else e += 1 - backwardX_R[n*R + i]; 
                    }
                    model.addConstr(e >= 1);
                }*/

                for (unsigned r = 0; r <= R; ++r) {
                    for (unsigned i = 0; i < n; ++i) {
                    cout << (forwardX_L[n*r + i].get(GRB_DoubleAttr_Xn) < 0.5 ? 0 : 1);
                    }
                    cout << " ";
                    for (unsigned i = 0; i < n; ++i) {
                        cout << (forwardX_R[n*r + i].get(GRB_DoubleAttr_Xn) < 0.5 ? 0 : 1);
                    }
                    cout <<  " | ";
                    for (unsigned i = 0; i < n; ++i) {
                        cout << (backwardX_L[n*r + i].get(GRB_DoubleAttr_Xn) < 0.5 ? 0 : 1);
                    }
                    cout << " ";
                    for (unsigned i = 0; i < n; ++i) {
                        cout << (backwardX_R[n*r + i].get(GRB_DoubleAttr_Xn) < 0.5 ? 0 : 1);
                    }
                    cout << endl;
                }
                cout << endl;
                for (unsigned r = 0; r <= R; ++r) {
                    for (unsigned i = 0; i < n; ++i) {
                    cout << (X_L[n*r + i].get(GRB_DoubleAttr_Xn) < 0.5 ? 0 : 1);
                    }
                    cout << " ";
                    for (unsigned i = 0; i < n; ++i) {
                        cout << (X_R[n*r + i].get(GRB_DoubleAttr_Xn) < 0.5 ? 0 : 1);
                    }

                    cout << endl;
                }
                break;

                //break;
            }
        }
        else {
            break;
        }
    }
    



    
}

int main(int argc, char const *argv[])
{
    //generateEQFA();
    modelSPECK(6, 32);
    return 0;
}
