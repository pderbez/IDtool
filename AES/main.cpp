#include <iostream>
#include <vector>
#include <set>


#include "/opt/gurobi912/linux64/include/gurobi_c++.h"

using namespace std;

void modelAES(unsigned rin, unsigned rdist, unsigned rout) {

    GRBEnv env = GRBEnv(true);
    env.set("LogFile", "mip1.log");
    env.start();

    GRBModel model = GRBModel(env);

    vector<GRBVar> forwardX (16*(rdist+1));
    vector<GRBVar> backwardX (16*(rdist+1));
    vector<GRBVar> Xin (16*(rin+1));
    vector<GRBVar> Xout (16*(rout+1));


    for (auto & x : forwardX) x = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
    for (auto & x : backwardX) x = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
    for (auto & x : Xin) x = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
    for (auto & x : Xout) x = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);

    for (unsigned i = 0; i < 16; ++i) model.addConstr(forwardX[i] == Xin[16*rin + i]);
    for (unsigned i = 0; i < 16; ++i) model.addConstr(backwardX[16*rdist + i] == Xout[i]);

    for (unsigned r = 0; r < rdist; ++r) {
        for (unsigned i = 0; i < 4; ++i) {
            for (unsigned j = 1; j < 4; ++j) model.addConstr(forwardX[16*(r+1) + 4*i + j] == forwardX[16*(r+1) + 4*i]);
            GRBLinExpr e = 0;
            for (unsigned j = 0; j < 4; ++j) e += forwardX[16*r + 4*((i+j)%4) + j];
            model.addConstr(forwardX[16*(r+1) + 4*i] <= e);
            model.addConstr(4*forwardX[16*(r+1) + 4*i] >= e);
        }
    }

    for (unsigned r = 0; r < rdist; ++r) {
        for (unsigned i = 0; i < 4; ++i) {
            for (unsigned j = 1; j < 4; ++j) model.addConstr(backwardX[16*r + 4*((i+j)%4) + j] == backwardX[16*r + 4*i]);
            GRBLinExpr e = 0;
            for (unsigned j = 0; j < 4; ++j) e += backwardX[16*(r+1) + 4*i + j];
            model.addConstr(backwardX[16*r + 4*i] <= e);
            model.addConstr(4*backwardX[16*r + 4*i] >= e);
        }
    }

    GRBLinExpr new_zeros = 0;

    for (unsigned r = 0; r < rdist; ++r) {
        for (unsigned i = 0; i < 4; ++i) {
            GRBLinExpr e = 0;
            for (unsigned j = 0; j < 4; ++j) e += forwardX[16*r + 4*((i+j)%4) + j];
            GRBLinExpr f = 0;
            for (unsigned j = 0; j < 4; ++j) f += backwardX[16*(r+1) + 4*i + j];
            GRBVar z = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
            model.addConstr(e >= z);
            model.addConstr(f >= z);
            model.addConstr(e+f <= 8 - 4*z);
            new_zeros += z;
        }
    }

    model.addConstr(new_zeros >= 1);

    GRBLinExpr proba = 0, dim = 0;

    for (unsigned i = 0; i < 4; ++i) {
        for (unsigned j = 1; j < 3; ++j) {
            GRBVar k = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
            dim -= k;
            GRBLinExpr e = 0;
            for (unsigned l = 0; l < 4; ++l) e += Xin[4*((j+l)%4) + l] + Xin[4*((j-1+l)%4) + l];
            model.addConstr(e + Xin[16 + 4*j + i] + Xin[16 + 4*(j-1) + i] + Xin[4*j + i] >= 11*k);
        }

        GRBVar k = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
        dim -= k;
        GRBLinExpr e = 0;
        for (unsigned l = 0; l < 4; ++l) e += Xin[4*l + l];
        model.addConstr(e + Xin[i] + Xin[4*3 + ((i+1)%4)] + Xin[16 + i] >= 7*k);

    }

    for (unsigned r = 0; r < rin; ++r) {
        for (unsigned i = 0; i < 4; ++i) {
            GRBLinExpr e = 0;
            for (unsigned j = 0; j < 4; ++j) e += Xin[16*r + 4*((i+j)%4) + j];
            GRBLinExpr f = 0;
            for (unsigned j = 0; j < 4; ++j) f += Xin[16*(r+1) + 4*i + j];
            GRBVar t = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
            model.addConstr(e + f <= 8*t);
            model.addConstr(e + f >= 5*t);

            if (r != 0 && r != rin-1) model.addConstr(e >= 4*t);

            proba += 4*t - f;
            dim += e;
        }
    }

    for (unsigned r = 0; r < rout; ++r) {
        for (unsigned i = 0; i < 4; ++i) {
            GRBLinExpr e = 0;
            for (unsigned j = 0; j < 4; ++j) e += Xout[16*r + 4*((i+j)%4) + j];
            GRBLinExpr f = 0;
            for (unsigned j = 0; j < 4; ++j) f += Xout[16*(r+1) + 4*i + j];
            GRBVar t = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
            model.addConstr(e + f <= 8*t);
            model.addConstr(e + f >= 5*t);

            if (r != 0 && r != rout-1) model.addConstr(f >= 4*t);

            proba += 4*t - e;
            dim += f;
        }
    }

    GRBLinExpr Din = 0, Dout = 0;
    for (unsigned i = 0; i < 16; ++i) Din += Xin[i];
    for (unsigned i = 0; i < 16; ++i) Dout += Xout[16*rout + i];

    GRBVar maxD = model.addVar(0.0, 128.0, 0.0, GRB_CONTINUOUS);
    {
        GRBVar tmp = model.addVar(0.0, 1.0, 0.0, GRB_BINARY);
        model.addConstr(maxD <= Din + 128.0*tmp);
        model.addConstr(maxD <= Dout + 128.0*(1-tmp));
    }

    model.addConstr(Din >= 1);
    model.addConstr(Dout >= 1);

    double coef_multiple = 0;
    proba -= coef_multiple/8;

    double coef_red = 3.0;

    GRBVar D = model.addVar(0.0, 128.0 + 32.0, 0.0, GRB_CONTINUOUS);
    GRBLinExpr N = 8*proba - 0.53 + coef_red;
    model.addConstr(D >= (N + 129.0 - 8.0*maxD)/2.0);
    model.addConstr(D >= N + 129.0 - 8.0*Din - 8.0*Dout);

    //model.addConstr(D <= 102);

    double coef_partial_enc = 5.13;

    GRBVar obj = model.addVar(0.0, 128.0 + 32.0, 0.0, GRB_CONTINUOUS);
    GRBLinExpr my_obj = obj;
    model.addConstr(obj >= D);
    model.addConstr(obj >= N - coef_partial_enc);
    model.addConstr(obj >= 8*dim - 8*proba + N - coef_partial_enc);

    model.setObjective(my_obj, GRB_MINIMIZE);


    model.optimize(); 

    for (unsigned i = 0; i < 4; ++i) {
        for (unsigned r = 0; r <= rin; ++r) {
            for (unsigned j = 0; j < 4; ++j) {
                cout << (Xin[16*r + 4*j + i].get(GRB_DoubleAttr_Xn) < 0.5 ? 0 : 1);
            }
            cout << "  ";
        }
        cout << endl;
    }
    cout << " ----- " << endl;
    for (unsigned i = 0; i < 4; ++i) {
        for (unsigned r = 0; r <= rdist; ++r) {
            for (unsigned j = 0; j < 4; ++j) {
                cout << (forwardX[16*r + 4*j + i].get(GRB_DoubleAttr_Xn) < 0.5 ? 0 : 1);
            }
            cout << "  ";
        }
        cout << endl;
    }
    cout << " ----- " << endl;
    for (unsigned i = 0; i < 4; ++i) {
        for (unsigned r = 0; r <= rdist; ++r) {
            for (unsigned j = 0; j < 4; ++j) {
                cout << (backwardX[16*r + 4*j + i].get(GRB_DoubleAttr_Xn) < 0.5 ? 0 : 1);
            }
            cout << "  ";
        }
        cout << endl;
    }
    cout << " ----- " << endl;
    for (unsigned i = 0; i < 4; ++i) {
        for (unsigned r = 0; r <= rout; ++r) {
            for (unsigned j = 0; j < 4; ++j) {
                cout << (Xout[16*r + 4*j + i].get(GRB_DoubleAttr_Xn) < 0.5 ? 0 : 1);
            }
            cout << "  ";
        }
        cout << endl;
    }
    cout << " ----- " << endl;
    cout << "D : " << D.get(GRB_DoubleAttr_Xn) << endl;

    
}

int main(int argc, char const *argv[])
{
    modelAES(2,3,1);
    return 0;
}
